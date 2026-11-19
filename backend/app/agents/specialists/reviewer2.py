"""AGENT 7: REVIEWER 2 (ADVERSARIAL CRITIQUE & CROSS-EXAMINATION).

Responsibilities:
- Challenge agent findings.
- Identify unsupported claims.
- Request additional evidence.
- Detect duplicated findings.
- Challenge incorrect assumptions.
- Identify missed scenarios.
"""

from typing import Any, Dict, List, Optional
from app.agents.specialists.base import BaseReviewAgent
from app.core.ai.base import LLMMessage, MessageRole, ModelConfig
from app.core.ai.gateway import ModelGateway
from app.orchestration.prompts import REVIEWER2_SYSTEM_PROMPT
from app.orchestration.state import (
    AgentCritique,
    DiscussionItem,
    FindingProposal,
    Reviewer2Output,
    ReviewState,
)


class Reviewer2Agent(BaseReviewAgent):
    """Adversarial cross-examination agent that scrutinizes proposed findings,
    demands code evidence, challenges hallucinations, and spots missed scenarios.
    """

    def __init__(self, gateway: Optional[ModelGateway] = None, timeout_seconds: float = 45.0):
        super().__init__(
            name="Reviewer 2",
            role="adversarial_critique",
            category="critique",
            gateway=gateway,
            timeout_seconds=timeout_seconds,
        )

    async def process(self, state: ReviewState) -> Dict[str, Any]:
        raw_diff = state.get("raw_diff", "")
        agent_findings: List[FindingProposal] = state.get("agent_findings", [])

        if not agent_findings:
            return {
                "agent_findings": [],
                "agent_discussions": [
                    DiscussionItem(
                        agent_name=self.name,
                        message_type="consensus",
                        content="Reviewer 2 evaluated the diff; no issues were proposed by specialists to challenge.",
                        is_verified=True,
                    )
                ],
                "tokens_used": 0,
                "cost_usd": 0.0,
                "reasoning_summary": "No specialist findings to critique.",
            }

        # Format findings for adversarial cross-examination
        proposals_text = "\n\n".join(
            f"Finding #{idx+1} [ID: {f.id}]:\n"
            f"  Agent: {f.agent_name}\n"
            f"  Title: {f.title}\n"
            f"  Category: {f.category} | Severity: {f.severity}\n"
            f"  Location: {f.file_path}:{f.line_number}\n"
            f"  Message: {f.message}\n"
            f"  Evidence: {f.code_evidence or 'None cited'}"
            for idx, f in enumerate(agent_findings)
        )

        diff_snippet = raw_diff[:8000]
        user_content = (
            f"Critique and challenge the following proposed findings from the specialist council.\n\n"
            f"PR Diff:\n```diff\n{diff_snippet}\n```\n\n"
            f"Proposed Findings to Evaluate:\n{proposals_text}\n\n"
            f"For each finding, determine if it is supported by code evidence, identify any "
            f"unwarranted assumptions or duplicates, and recommend 'approve', 'reject', or 'modify'. "
            f"Also identify any missed critical scenarios."
        )

        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=REVIEWER2_SYSTEM_PROMPT),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]

        response = await self.gateway.generate_structured(
            messages=messages,
            response_model=Reviewer2Output,
            config=ModelConfig(temperature=0.1, timeout_seconds=self.timeout_seconds),
        )

        data: Reviewer2Output = response.data
        discussions: List[DiscussionItem] = []

        # Convert critiques into inter-agent discussion messages
        for critique in data.critiques:
            msg_type = "critique" if critique.suggested_action in ("reject", "modify") else "consensus"
            discussions.append(
                DiscussionItem(
                    finding_id=critique.finding_id,
                    finding_title=critique.finding_title,
                    agent_name=self.name,
                    message_type=msg_type,
                    content=(
                        f"Reviewer 2 [{critique.suggested_action.upper()}]: {critique.challenge_reason}"
                    ),
                    is_verified=(critique.suggested_action == "approve"),
                )
            )

        # Record missed scenario discussion if any detected
        for missed in data.missed_scenarios:
            discussions.append(
                DiscussionItem(
                    agent_name=self.name,
                    message_type="dissent",
                    content=f"Reviewer 2 identified unaddressed edge case: {missed}",
                    is_verified=False,
                )
            )

        return {
            "agent_findings": [],  # Reviewer 2 critiques existing findings rather than inventing new ones
            "agent_discussions": discussions,
            "tokens_used": response.usage.total_tokens,
            "cost_usd": response.cost_usd,
            "reasoning_summary": data.reasoning_summary or f"Cross-examined {len(agent_findings)} findings.",
        }
