"""LangGraph Multi-Agent Code Review Workflow.

Defines the complete state machine orchestrating:
1. Context Agent
2. Parallel Specialists (Bug Hunter, Security, Performance, Architecture, Test)
3. Reviewer 2 (Adversarial Cross-Examination)
4. Verification Arbiter (Consensus & Evidence Validation)
5. Review Finalizer (Scoring & Markdown Summary Generation)
"""

import asyncio
from typing import Any, Dict, List, Optional
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.agents.specialists import (
    ArchitectureAgent,
    BugHunterAgent,
    ContextAgent,
    PerformanceAgent,
    Reviewer2Agent,
    SecurityAgent,
    TestAgent,
    VerificationAgent,
)
from app.core.ai.gateway import ModelGateway
from app.core.logging import get_logger
from app.orchestration.registry import AgentMetadata, get_agent_registry
from app.orchestration.state import (
    AgentLogEntry,
    DiscussionItem,
    FindingProposal,
    ReviewState,
    VerifiedFinding,
)

logger = get_logger("openreview.orchestration.workflow")


def calculate_review_scores(verified_findings: List[VerifiedFinding]) -> Dict[str, float]:
    """Calculates overall and category-specific quality scores (0.0 - 100.0)."""
    severity_penalties = {
        "critical": 25.0,
        "high": 15.0,
        "medium": 8.0,
        "low": 3.0,
        "info": 0.0,
    }

    overall = 100.0
    sec_deductions = 0.0
    perf_deductions = 0.0
    quality_deductions = 0.0

    for vf in verified_findings:
        if vf.status != "verified":
            continue
        penalty = severity_penalties.get(vf.finding.severity, 5.0)
        overall -= penalty

        cat = vf.finding.category
        if cat == "security":
            sec_deductions += penalty * 1.2
        elif cat == "performance":
            perf_deductions += penalty * 1.2
        elif cat in ("bug", "architecture", "test"):
            quality_deductions += penalty

    return {
        "overall_score": max(0.0, min(100.0, round(overall, 1))),
        "security_score": max(0.0, min(100.0, round(100.0 - sec_deductions, 1))),
        "performance_score": max(0.0, min(100.0, round(100.0 - perf_deductions, 1))),
        "quality_score": max(0.0, min(100.0, round(100.0 - quality_deductions, 1))),
    }


def generate_markdown_summary(
    state: ReviewState,
    scores: Dict[str, float],
    verified_findings: List[VerifiedFinding],
) -> str:
    """Renders a rich executive markdown summary of the multi-agent code review pass."""
    total_findings = len([vf for vf in verified_findings if vf.status == "verified"])
    uncertain_count = len([vf for vf in verified_findings if vf.status == "uncertain"])
    rejected_count = len([vf for vf in verified_findings if vf.status == "rejected"])

    score_badge = (
        "🟢 PASS" if scores["overall_score"] >= 80 else
        ("🟡 WARNING" if scores["overall_score"] >= 60 else "🔴 ACTION REQUIRED")
    )

    summary_lines = [
        f"# 🤖 OpenReview AI Code Review Summary — {score_badge}",
        "",
        f"**Pull Request:** {state.get('pr_title', 'Pull Request')}",
        f"**Commit:** `{state.get('commit_sha', 'HEAD')[:8]}` | **Status:** Completed",
        "",
        "### 📊 Review Scorecard",
        f"- **Overall Quality Score:** **{scores['overall_score']} / 100**",
        f"- **Security Posture:** **{scores['security_score']} / 100**",
        f"- **Performance Health:** **{scores['performance_score']} / 100**",
        f"- **Code & Test Quality:** **{scores['quality_score']} / 100**",
        "",
        f"**Verified Issues:** {total_findings} | **Uncertain Findings:** {uncertain_count} | **Rejected (False Positives):** {rejected_count}",
        "",
        "---",
        "### 🛡️ Verified Actionable Findings",
    ]

    actionable = [vf for vf in verified_findings if vf.status == "verified"]
    if not actionable:
        summary_lines.append("\n✅ **No critical defects or security vulnerabilities detected in these changes.**\n")
    else:
        for idx, vf in enumerate(actionable, start=1):
            f = vf.finding
            summary_lines.extend([
                f"\n#### {idx}. [{f.severity.upper()}] {f.title} (`{f.file_path}:{f.line_number}`)",
                f"- **Category:** `{f.category}` | **Agent:** {f.agent_name} | **Confidence:** {int(vf.confidence_score * 100)}%",
                f"- **Issue:** {f.message}",
            ])
            if f.suggested_patch:
                summary_lines.extend([
                    "- **Suggested Patch:**",
                    "```suggestion",
                    f.suggested_patch.strip(),
                    "```",
                ])

    summary_lines.extend([
        "",
        "---",
        "### 🏛️ Multi-Agent Council & Inter-Agent Conference",
        "The review was conducted autonomously with cross-examination by:",
        "- **Context Agent**: Repository AST & diff analysis",
        "- **Bug Hunter**: Functional correctness & logic checks",
        "- **Security Sentinel**: OWASP Top 10 & CWE vulnerability analysis",
        "- **Performance Guardian**: Algorithmic complexity & DB efficiency",
        "- **Architecture Specialist**: Clean architecture & separation of concerns",
        "- **Test Guardian**: Test coverage & regression risk evaluation",
        "- **Reviewer 2**: Adversarial challenge & evidence verification",
        "- **Verification Arbiter**: Final consensus judge & reachability audit",
    ])

    return "\n".join(summary_lines)


class ReviewWorkflowBuilder:
    """Builds and compiles the LangGraph StateGraph review workflow."""

    def __init__(self, gateway: Optional[ModelGateway] = None):
        self.gateway = gateway or ModelGateway()
        self._register_default_agents()

    def _register_default_agents(self):
        """Populates the agent registry with the default eight agents."""
        registry = get_agent_registry()

        # Check if already populated
        if registry.get("context agent"):
            return

        # 1. Context Agent
        registry.register(
            ContextAgent(self.gateway),
            AgentMetadata(
                name="Context Agent",
                role="context_retrieval",
                category="context",
                description="Understands PR and indexes code context",
                is_specialist=False,
                priority=10,
            ),
        )

        # 2. Bug Hunter
        registry.register(
            BugHunterAgent(self.gateway),
            AgentMetadata(
                name="Bug Hunter",
                role="bug_detection",
                category="bug",
                description="Detects logic bugs, null references, and race conditions",
                is_specialist=True,
                priority=20,
            ),
        )

        # 3. Security Agent
        registry.register(
            SecurityAgent(self.gateway),
            AgentMetadata(
                name="Security Sentinel",
                role="security_analysis",
                category="security",
                description="Detects SQLi, RCE, auth flaws, and exposed secrets",
                is_specialist=True,
                priority=21,
            ),
        )

        # 4. Performance Agent
        registry.register(
            PerformanceAgent(self.gateway),
            AgentMetadata(
                name="Performance Guardian",
                role="performance_profiling",
                category="performance",
                description="Detects algorithmic bottlenecks, N+1 queries, and leaks",
                is_specialist=True,
                priority=22,
            ),
        )

        # 5. Architecture Agent
        registry.register(
            ArchitectureAgent(self.gateway),
            AgentMetadata(
                name="Architecture Specialist",
                role="architecture_review",
                category="architecture",
                description="Evaluates coupling, SRP, API design, and error handling",
                is_specialist=True,
                priority=23,
            ),
        )

        # 6. Test Agent
        registry.register(
            TestAgent(self.gateway),
            AgentMetadata(
                name="Test Guardian",
                role="test_coverage",
                category="test",
                description="Evaluates regression risks and test coverage",
                is_specialist=True,
                priority=24,
            ),
        )

        # 7. Reviewer 2
        registry.register(
            Reviewer2Agent(self.gateway),
            AgentMetadata(
                name="Reviewer 2",
                role="adversarial_critique",
                category="critique",
                description="Challenges specialist findings and eliminates false positives",
                is_specialist=False,
                priority=50,
            ),
        )

        # 8. Verification Agent
        registry.register(
            VerificationAgent(self.gateway),
            AgentMetadata(
                name="Verification Arbiter",
                role="verification_arbiter",
                category="verification",
                description="Arbitrates consensus and verifies source code evidence",
                is_specialist=False,
                priority=60,
            ),
        )

    def build(self) -> CompiledStateGraph:
        """Constructs and compiles the StateGraph workflow."""
        builder = StateGraph(ReviewState)
        registry = get_agent_registry()

        # Step 1: Add Context Node
        context_agent = registry.get("context agent")
        builder.add_node("context_node", context_agent.execute)
        builder.add_edge(START, "context_node")

        # Step 2: Add Parallel Specialist Nodes
        specialist_nodes = []
        for agent, meta in registry.list_specialists():
            node_name = f"specialist_{meta.category}"
            builder.add_node(node_name, agent.execute)
            builder.add_edge("context_node", node_name)
            specialist_nodes.append(node_name)

        # Step 3: Add Reviewer 2 (Adversarial Critique Node)
        reviewer2 = registry.get("reviewer 2")
        builder.add_node("reviewer2_node", reviewer2.execute)
        for s_node in specialist_nodes:
            builder.add_edge(s_node, "reviewer2_node")

        # Step 4: Add Verification Arbiter Node
        verification_agent = registry.get("verification arbiter")
        builder.add_node("verification_node", verification_agent.execute)
        builder.add_edge("reviewer2_node", "verification_node")

        # Step 5: Add Finalize Review Node
        async def finalize_review(state: ReviewState) -> Dict[str, Any]:
            verified_findings = state.get("verified_findings", [])
            scores = calculate_review_scores(verified_findings)
            summary = generate_markdown_summary(state, scores, verified_findings)

            return {
                "overall_score": scores["overall_score"],
                "security_score": scores["security_score"],
                "performance_score": scores["performance_score"],
                "quality_score": scores["quality_score"],
                "review_summary": summary,
                "is_completed": True,
            }

        builder.add_node("finalize_node", finalize_review)
        builder.add_edge("verification_node", "finalize_node")
        builder.add_edge("finalize_node", END)

        return builder.compile()


# Global workflow singleton
_workflow_graph: Optional[CompiledStateGraph] = None


def get_review_workflow(gateway: Optional[ModelGateway] = None) -> CompiledStateGraph:
    """Returns the compiled LangGraph workflow instance."""
    global _workflow_graph
    if _workflow_graph is None or gateway is not None:
        builder = ReviewWorkflowBuilder(gateway)
        _workflow_graph = builder.build()
    return _workflow_graph
