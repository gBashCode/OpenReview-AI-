"""AGENT 4: PERFORMANCE AGENT.

Responsibilities:
- Analyze algorithmic complexity.
- Identify inefficient database queries.
- Detect unnecessary loops.
- Detect memory problems.
- Identify expensive operations.
"""

from typing import Any, Dict, List, Optional
from app.agents.specialists.base import BaseReviewAgent
from app.core.ai.base import LLMMessage, MessageRole, ModelConfig
from app.core.ai.gateway import ModelGateway
from app.orchestration.prompts import PERFORMANCE_AGENT_SYSTEM_PROMPT
from app.orchestration.state import (
    AgentFindingList,
    DiscussionItem,
    FindingProposal,
    ReviewState,
)


class PerformanceAgent(BaseReviewAgent):
    """Detects algorithmic bottlenecks, N+1 query patterns, excessive allocations,
    memory leaks, and blocking I/O calls.
    """

    def __init__(self, gateway: Optional[ModelGateway] = None, timeout_seconds: float = 45.0):
        super().__init__(
            name="Performance Guardian",
            role="performance_profiling",
            category="performance",
            gateway=gateway,
            timeout_seconds=timeout_seconds,
        )

    async def process(self, state: ReviewState) -> Dict[str, Any]:
        raw_diff = state.get("raw_diff", "")
        context_evidence = state.get("context_evidence", {})

        if not raw_diff:
            return {
                "agent_findings": [],
                "agent_discussions": [],
                "tokens_used": 0,
                "cost_usd": 0.0,
                "reasoning_summary": "No diff provided to inspect.",
            }

        diff_snippet = raw_diff[:9000]
        context_brief = context_evidence.get("pr_purpose", "Code changes")

        user_content = (
            f"Analyze the following Pull Request changes for performance inefficiencies, "
            f"algorithmic complexity issues, unindexed or N+1 database queries, redundant loops, "
            f"memory leaks, and blocking operations in asynchronous paths.\n\n"
            f"Context Summary: {context_brief}\n\n"
            f"Git Unified Diff:\n```diff\n{diff_snippet}\n```\n\n"
            f"Provide your structured findings conforming to AgentFindingList."
        )

        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=PERFORMANCE_AGENT_SYSTEM_PROMPT),
            LLMMessage(role=MessageRole.USER, content=user_content),
        ]

        response = await self.gateway.generate_structured(
            messages=messages,
            response_model=AgentFindingList,
            config=ModelConfig(temperature=0.1, timeout_seconds=self.timeout_seconds),
        )

        data: AgentFindingList = response.data
        findings: List[FindingProposal] = []
        discussions: List[DiscussionItem] = []

        for f in data.findings:
            f.agent_name = self.name
            f.category = "performance"
            findings.append(f)

            discussions.append(
                DiscussionItem(
                    finding_id=f.id,
                    finding_title=f.title,
                    agent_name=self.name,
                    message_type="proposal",
                    content=f"Performance alert: {f.title} ({f.severity}) - {f.message[:150]}...",
                    file_context=f"{f.file_path}:{f.line_number}",
                )
            )

        return {
            "agent_findings": findings,
            "agent_discussions": discussions,
            "tokens_used": response.usage.total_tokens,
            "cost_usd": response.cost_usd,
            "reasoning_summary": data.reasoning_summary or f"Identified {len(findings)} performance opportunities.",
        }
