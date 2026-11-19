"""AGENT 1: CONTEXT AGENT.

Responsibilities:
- Understand the PR.
- Retrieve relevant repository context.
- Identify affected code.
- Prepare context for other agents.
"""

from typing import Any, Dict, List, Optional
from app.agents.specialists.base import BaseReviewAgent
from app.analyzer.diff_parser import UnifiedDiffParser
from app.core.ai.base import LLMMessage, MessageRole, ModelConfig
from app.core.ai.gateway import ModelGateway
from app.core.logging import get_logger
from app.orchestration.prompts import CONTEXT_AGENT_SYSTEM_PROMPT
from app.orchestration.state import AgentLogEntry, DiscussionItem, ReviewState
from pydantic import BaseModel, Field

logger = get_logger("openreview.agents.context")


class PRContextSummary(BaseModel):
    """Structured LLM analysis of PR intent and scope."""

    pr_purpose: str = Field(description="Primary objective of this Pull Request")
    architecture_impact: str = Field(description="Systems, modules, and interfaces affected")
    critical_files: List[str] = Field(default_factory=list, description="High-risk or core files touched")
    suggested_focus_areas: List[str] = Field(default_factory=list, description="Specific areas specialists must inspect")


class ContextAgent(BaseReviewAgent):
    """Understands the PR, extracts changed files, queries repository intelligence,
    and structures context evidence for specialist agents.
    """

    def __init__(self, gateway: Optional[ModelGateway] = None, timeout_seconds: float = 45.0):
        super().__init__(
            name="Context Agent",
            role="context_retrieval",
            category="context",
            gateway=gateway,
            timeout_seconds=timeout_seconds,
        )

    async def process(self, state: ReviewState) -> Dict[str, Any]:
        raw_diff = state.get("raw_diff", "")
        changed_files = state.get("changed_files", [])

        # Parse unified git diff if not already parsed
        if not changed_files and raw_diff:
            diff_parser = UnifiedDiffParser()
            file_diffs = diff_parser.parse(raw_diff)
            changed_files = [
                {
                    "file_path": fd.new_path or fd.old_path or "unknown",
                    "change_type": fd.status,
                    "additions": fd.additions,
                    "deletions": fd.deletions,
                    "modified_lines": fd.modified_line_numbers,
                    "patch": fd.raw_patch[:3000] if fd.raw_patch else "",
                }
                for fd in file_diffs
            ]

        # Prepare context evidence
        context_evidence = state.get("context_evidence", {}) or {}
        pr_analysis = state.get("pr_analysis", {}) or {}

        # Synthesize context brief using LLM
        tokens_used = 0
        cost_usd = 0.0
        reasoning = "Repository context and changed files structured successfully."

        if raw_diff:
            diff_snippet = raw_diff[:8000]
            user_prompt = (
                f"PR Title: {state.get('pr_title', 'Pull Request')}\n"
                f"PR Description: {state.get('pr_description', 'No description provided.')}\n\n"
                f"Unified Git Diff Snippet:\n```diff\n{diff_snippet}\n```\n\n"
                f"Analyze this Pull Request and return the structured PRContextSummary."
            )

            messages = [
                LLMMessage(role=MessageRole.SYSTEM, content=CONTEXT_AGENT_SYSTEM_PROMPT),
                LLMMessage(role=MessageRole.USER, content=user_prompt),
            ]

            try:
                response = await self.gateway.generate_structured(
                    messages=messages,
                    response_model=PRContextSummary,
                    config=ModelConfig(temperature=0.1, timeout_seconds=self.timeout_seconds),
                )
                tokens_used = response.usage.total_tokens
                cost_usd = response.cost_usd
                summary_data: PRContextSummary = response.data

                # Enrich context evidence with synthesized understanding
                context_evidence["pr_purpose"] = summary_data.pr_purpose
                context_evidence["architecture_impact"] = summary_data.architecture_impact
                context_evidence["critical_files"] = summary_data.critical_files
                context_evidence["suggested_focus_areas"] = summary_data.suggested_focus_areas
                reasoning = f"Context extracted: {summary_data.pr_purpose}"

            except Exception as e:
                logger.warning(f"ContextAgent LLM synthesis skipped/failed: {e}")
                context_evidence["pr_purpose"] = state.get("pr_title", "Pull Request changes")

        # Discussion item announcing completion of context preparation
        file_count = len(changed_files)
        discussion = DiscussionItem(
            agent_name=self.name,
            message_type="proposal",
            content=(
                f"Context Agent indexed {file_count} changed files. "
                f"Prepared context evidence for specialist council."
            ),
            is_verified=True,
        )

        return {
            "changed_files": changed_files,
            "context_evidence": context_evidence,
            "pr_analysis": pr_analysis,
            "agent_findings": [],
            "agent_discussions": [discussion],
            "tokens_used": tokens_used,
            "cost_usd": cost_usd,
            "reasoning_summary": reasoning,
        }
