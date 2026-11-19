"""Base Specialist Review Agent Architecture.

Enforces execution isolation, token budgeting, timeouts, structured output parsing,
and resilient partial-failure handling.
"""

from abc import ABC, abstractmethod
import asyncio
import time
from typing import Any, Dict, List, Optional
from app.core.ai.base import LLMMessage, MessageRole, ModelConfig
from app.core.ai.gateway import ModelGateway
from app.core.config import get_settings
from app.core.logging import get_logger
from app.orchestration.state import AgentLogEntry, DiscussionItem, FindingProposal, ReviewState

logger = get_logger("openreview.agents.specialist")
settings = get_settings()


class BaseReviewAgent(ABC):
    """Abstract base class for all AI review agents participating in the multi-agent council."""

    def __init__(
        self,
        name: str,
        role: str,
        category: str,
        gateway: Optional[ModelGateway] = None,
        timeout_seconds: float = 45.0,
        model_name: Optional[str] = None,
    ):
        self.name = name
        self.role = role
        self.category = category
        self.gateway = gateway or ModelGateway()
        self.timeout_seconds = timeout_seconds
        self.model_name = model_name or settings.DEFAULT_MODEL

    @abstractmethod
    async def process(self, state: ReviewState) -> Dict[str, Any]:
        """Core agent logic to be implemented by each specialized agent."""
        pass

    async def execute(self, state: ReviewState) -> Dict[str, Any]:
        """Executes agent processing with timeout guards, telemetry, and partial failure isolation.

        Ensures that an agent crash or timeout never terminates the entire review workflow.
        """
        start_time = time.time()
        logger.info(f"Agent '{self.name}' starting execution for review {state.get('review_id')}")

        try:
            # Enforce timeout guard
            result = await asyncio.wait_for(
                self.process(state),
                timeout=self.timeout_seconds,
            )

            execution_time_ms = int((time.time() - start_time) * 1000)
            findings_count = len(result.get("agent_findings", []))

            # Record successful telemetry log
            log_entry = AgentLogEntry(
                agent_name=self.name,
                role=self.role,
                status="completed",
                execution_time_ms=execution_time_ms,
                tokens_used=result.get("tokens_used", 0),
                cost_usd=result.get("cost_usd", 0.0),
                findings_count=findings_count,
                reasoning_summary=result.get("reasoning_summary", f"{self.name} completed successfully."),
            )

            # Ensure agent_execution_logs list is populated
            current_logs = result.get("agent_execution_logs", [])
            current_logs.append(log_entry)
            result["agent_execution_logs"] = current_logs

            logger.info(
                f"Agent '{self.name}' completed in {execution_time_ms}ms "
                f"({findings_count} findings)"
            )
            return result

        except asyncio.TimeoutError:
            execution_time_ms = int((time.time() - start_time) * 1000)
            err_msg = f"Agent '{self.name}' timed out after {self.timeout_seconds}s"
            logger.warning(err_msg)

            log_entry = AgentLogEntry(
                agent_name=self.name,
                role=self.role,
                status="timed_out",
                execution_time_ms=execution_time_ms,
                error_message=err_msg,
            )
            return {
                "agent_findings": [],
                "agent_discussions": [],
                "agent_execution_logs": [log_entry],
                "errors": [err_msg],
            }

        except Exception as exc:
            execution_time_ms = int((time.time() - start_time) * 1000)
            err_msg = f"Agent '{self.name}' failed with error: {str(exc)}"
            logger.error(err_msg, exc_info=True)

            log_entry = AgentLogEntry(
                agent_name=self.name,
                role=self.role,
                status="failed",
                execution_time_ms=execution_time_ms,
                error_message=err_msg,
            )
            return {
                "agent_findings": [],
                "agent_discussions": [],
                "agent_execution_logs": [log_entry],
                "errors": [err_msg],
            }
