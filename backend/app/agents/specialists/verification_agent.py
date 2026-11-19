"""AGENT 8: VERIFICATION AGENT (ARBITER & CONSENSUS ENGINE).

Responsibilities:
- Validate findings against source code.
- Check relevant execution paths.
- Evaluate available static analysis results.
- Check whether the issue is reproducible.
- Reject unsupported findings.
- Classify verified and uncertain findings.
"""

from typing import Any, Dict, List, Optional
from app.agents.specialists.base import BaseReviewAgent
from app.core.ai.base import LLMMessage, MessageRole, ModelConfig
from app.core.ai.gateway import ModelGateway
from app.orchestration.deduplication import FindingDeduplicator
from app.orchestration.prompts import VERIFICATION_AGENT_SYSTEM_PROMPT
from app.orchestration.state import (
    DiscussionItem,
    FindingProposal,
    ReviewState,
    VerificationOutput,
    VerifiedFinding,
)


class VerificationAgent(BaseReviewAgent):
    """Consensus arbiter that inspects specialist findings and Reviewer 2 critiques,
    verifies source code execution paths, rejects hallucinations, and produces the verified verdict.
    """

    def __init__(self, gateway: Optional[ModelGateway] = None, timeout_seconds: float = 45.0):
        super().__init__(
            name="Verification Arbiter",
            role="verification_arbiter",
            category="verification",
            gateway=gateway,
            timeout_seconds=timeout_seconds,
        )

    async def process(self, state: ReviewState) -> Dict[str, Any]:
        raw_diff = state.get("raw_diff", "")
        raw_findings: List[FindingProposal] = state.get("agent_findings", [])
        discussions: List[DiscussionItem] = state.get("agent_discussions", [])

        # Step 1: Pre-filter and deduplicate findings using proximity deduplicator
        deduped_findings, dedup_discussions = FindingDeduplicator.deduplicate(raw_findings)

        if not deduped_findings:
            return {
                "verified_findings": [],
                "agent_discussions": dedup_discussions + [
                    DiscussionItem(
                        agent_name=self.name,
                        message_type="verification",
                        content="Verification Arbiter found 0 actionable findings after deduplication.",
                        is_verified=True,
                    )
                ],
                "tokens_used": 0,
                "cost_usd": 0.0,
                "reasoning_summary": "No findings required arbitration.",
            }

        # Step 2: Format findings and Reviewer 2 debates for the Verification Arbiter
        proposals_summary = "\n\n".join(
            f"Finding #{idx+1} [ID: {f.id}]:\n"
            f"  Agent: {f.agent_name} | Category: {f.category} | Severity: {f.severity}\n"
            f"  Target: {f.file_path}:{f.line_number}\n"
            f"  Title: {f.title}\n"
            f"  Message: {f.message}\n"
            f"  Evidence: {f.code_evidence or 'N/A'}"
            for idx, f in enumerate(deduped_findings)
        )

        critiques_summary = "\n".join(
            f"- [{d.agent_name}] {d.content}"
            for d in discussions
            if d.message_type in ("critique", "dissent")
        ) or "None recorded."

        diff_snippet = raw_diff[:8000]
        user_content = (
            f"Conduct final verification arbitration for these findings.\n\n"
            f"Git Unified Diff:\n```diff\n{diff_snippet}\n```\n\n"
            f"Deduplicated Findings to Verify:\n{proposals_summary}\n\n"
            f"Reviewer 2 Critiques & Inter-Agent Debate:\n{critiques_summary}\n\n"
            f"Evaluate each finding against source code evidence. Trace execution paths, "
            f"reject unsupported claims or hallucinations, and classify each into "
            f"'verified', 'uncertain', or 'rejected'. Provide calibrated confidence scores."
        )

        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=VERIFICATION_AGENT_SYSTEM_PROMPT),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]

        response = await self.gateway.generate_structured(
            messages=messages,
            response_model=VerificationOutput,
            config=ModelConfig(temperature=0.1, timeout_seconds=self.timeout_seconds),
        )

        data: VerificationOutput = response.data
        new_discussions: List[DiscussionItem] = list(dedup_discussions)

        # Record verification decisions in inter-agent conference
        for vf in data.verified_findings:
            msg_type = "verification" if vf.status == "verified" else "dissent"
            new_discussions.append(
                DiscussionItem(
                    finding_id=vf.finding.id,
                    finding_title=vf.finding.title,
                    agent_name=self.name,
                    message_type=msg_type,
                    content=(
                        f"Verdict [{vf.status.upper()} - {int(vf.confidence_score * 100)}% conf]: "
                        f"{vf.verification_reason}"
                    ),
                    file_context=f"{vf.finding.file_path}:{vf.finding.line_number}",
                    is_verified=(vf.status == "verified"),
                )
            )

        if data.consensus_notes:
            new_discussions.append(
                DiscussionItem(
                    agent_name=self.name,
                    message_type="consensus",
                    content=f"Consensus Arbiter Notes: {data.consensus_notes}",
                    is_verified=True,
                )
            )

        return {
            "verified_findings": data.verified_findings,
            "agent_discussions": new_discussions,
            "tokens_used": response.usage.total_tokens,
            "cost_usd": response.cost_usd,
            "reasoning_summary": data.reasoning_summary or f"Arbitrated {len(data.verified_findings)} findings.",
        }
