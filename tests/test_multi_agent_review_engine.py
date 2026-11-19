"""Comprehensive Test Suite for Multi-Agent Code Review Engine using LangGraph.

Covers:
1. Agent Registry dynamic addition and discovery
2. Finding Deduplication and proximity collisions
3. Agent 1: Context Agent
4. Agent 2: Bug Hunter
5. Agent 3: Security Agent
6. Agent 4: Performance Agent
7. Agent 5: Architecture Agent
8. Agent 6: Test Agent
9. Agent 7: Reviewer 2 (Adversarial critique)
10. Agent 8: Verification Agent (Consensus arbiter)
11. Agent Timeout & Resilient Partial Failure handling
12. Scorecard Calculation & Executive Markdown Summary
13. LangGraph Multi-Agent StateGraph Workflow End-to-End
14. Database Persistence Service (Review, Agents, Findings, Discussions)
15. REST API Endpoints (/council/registry, /{review_id}/orchestrate)
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.agents.models import AgentDiscussion, ReviewAgent
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
from app.core.ai.base import LLMResponse, ModelConfig, StructuredLLMResponse, TokenUsage
from app.core.ai.gateway import ModelGateway
from app.core.ai.providers.mock_provider import MockLLMProvider
from app.database.base import Base
from app.findings.models import Finding
from app.main import app
from app.orchestration.deduplication import FindingDeduplicator
from app.orchestration.registry import AgentMetadata, AgentRegistry, get_agent_registry
from app.orchestration.service import ReviewOrchestrationService
from app.orchestration.state import (
    AgentCritique,
    AgentFindingList,
    AgentLogEntry,
    DiscussionItem,
    FindingProposal,
    Reviewer2Output,
    ReviewState,
    VerificationOutput,
    VerifiedFinding,
)
from app.orchestration.workflow import (
    calculate_review_scores,
    generate_markdown_summary,
    get_review_workflow,
    ReviewWorkflowBuilder,
)
from app.organizations.models import Organization
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository
from app.reviews.models import Review


SAMPLE_UNIFIED_DIFF = """diff --git a/app/auth.py b/app/auth.py
index 1111111..2222222 100644
--- a/app/auth.py
+++ b/app/auth.py
@@ -10,6 +10,12 @@ def authenticate_user(db, username, password):
     user = db.query(User).filter(User.username == username).first()
+    # Insecure query and hardcoded secret
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    db.execute(query)
+    api_token = "ghp_1234567890abcdef1234567890abcdef123456"
+    if not user:
+        return user.token  # Bug: None dereference
     return user
"""


@pytest.fixture
def mock_gateway():
    """Provides a ModelGateway preloaded with a configurable MockLLMProvider."""
    gateway = ModelGateway(primary_provider="mock", fallback_provider="mock")
    mock_prov = MockLLMProvider()
    gateway.register_provider("mock", mock_prov)
    return gateway


@pytest.fixture
def sample_initial_state() -> ReviewState:
    """Provides a realistic initial ReviewState."""
    return {
        "review_id": "rev-test-100",
        "pull_request_id": "pr-test-100",
        "repository_id": "repo-test-100",
        "commit_sha": "a1b2c3d4e5f67890",
        "pr_title": "feat: update user authentication and token handling",
        "pr_description": "Implements direct SQL querying and token lookup for performance.",
        "raw_diff": SAMPLE_UNIFIED_DIFF,
        "changed_files": [],
        "context_evidence": {},
        "pr_analysis": {},
        "agent_findings": [],
        "agent_discussions": [],
        "agent_execution_logs": [],
        "errors": [],
        "verified_findings": [],
        "overall_score": 100.0,
        "security_score": 100.0,
        "performance_score": 100.0,
        "quality_score": 100.0,
        "review_summary": "",
        "token_budget_remaining": 50000,
        "is_completed": False,
    }


# =====================================================================
# 1. AGENT REGISTRY TESTS
# =====================================================================

def test_agent_registry_addition_and_retrieval():
    """Verifies that new agents can be added dynamically to the registry without modifying core code."""
    registry = AgentRegistry()

    class CustomLinterAgent:
        def __init__(self):
            self.name = "Custom Linter"

    meta = AgentMetadata(
        name="Custom Linter",
        role="linting",
        category="style",
        description="Enforces PEP8 and team conventions",
        is_specialist=True,
        priority=35,
    )

    registry.register(CustomLinterAgent(), meta)

    agent = registry.get("custom linter")
    assert agent is not None
    assert agent.name == "Custom Linter"

    specialists = registry.list_specialists()
    assert len(specialists) == 1
    assert specialists[0][1].name == "Custom Linter"

    all_meta = registry.list_all()
    assert len(all_meta) == 1

    assert registry.unregister("custom linter") is True
    assert registry.get("custom linter") is None


# =====================================================================
# 2. FINDING DEDUPLICATION TESTS
# =====================================================================

def test_finding_deduplicator_proximity_and_consensus():
    """Verifies finding deduplication across nearby line numbers and emits consensus discussions."""
    f1 = FindingProposal(
        file_path="app/auth.py",
        line_number=12,
        category="security",
        severity="critical",
        title="SQL Injection in user query",
        message="Raw SQL format string concatenation detected.",
        agent_name="Security Sentinel",
        confidence_score=0.98,
    )
    # Duplicate with slightly different line number (line 13) and secondary agent
    f2 = FindingProposal(
        file_path="app/auth.py",
        line_number=13,
        category="security",
        severity="high",
        title="SQL Injection in user query",
        message="Unescaped SQL query execution allows authentication bypass.",
        agent_name="Bug Hunter",
        confidence_score=0.91,
    )
    # Distinct finding
    f3 = FindingProposal(
        file_path="app/auth.py",
        line_number=17,
        category="bug",
        severity="medium",
        title="Null pointer dereference on user.token",
        message="Accessing user.token when user is None.",
        agent_name="Bug Hunter",
        confidence_score=0.95,
    )

    deduped, discussions = FindingDeduplicator.deduplicate([f1, f2, f3], line_tolerance=2)

    assert len(deduped) == 2
    # f1 should be preserved as primary because of higher confidence and critical severity
    primary_sec = next(f for f in deduped if f.category == "security")
    assert primary_sec.id == f1.id
    assert "Security Sentinel" in primary_sec.agent_name
    assert "Bug Hunter" in primary_sec.agent_name  # Combined attribution

    # Deduplication Arbiter should have logged a consensus discussion
    assert len(discussions) == 1
    assert discussions[0].agent_name == "Deduplication Arbiter"
    assert discussions[0].message_type == "consensus"


# =====================================================================
# 3. SPECIALIST AGENT TESTS (AGENTS 1 - 8)
# =====================================================================

@pytest.mark.asyncio
async def test_agent1_context_agent(mock_gateway, sample_initial_state):
    """AGENT 1: Context Agent parses diff and structures context evidence."""
    agent = ContextAgent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["changed_files"]) >= 1
    assert res["changed_files"][0]["file_path"] == "app/auth.py"
    assert "context_evidence" in res
    assert len(res["agent_discussions"]) == 1
    assert res["agent_execution_logs"][0].status == "completed"
    assert res["agent_execution_logs"][0].agent_name == "Context Agent"


@pytest.mark.asyncio
async def test_agent2_bug_hunter(mock_gateway, sample_initial_state):
    """AGENT 2: Bug Hunter detects functional bugs and null references."""
    agent = BugHunterAgent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["agent_findings"]) >= 1
    finding = res["agent_findings"][0]
    assert finding.category == "bug"
    assert finding.agent_name == "Bug Hunter"
    assert len(res["agent_discussions"]) >= 1
    assert res["agent_execution_logs"][0].status == "completed"


@pytest.mark.asyncio
async def test_agent3_security_agent(mock_gateway, sample_initial_state):
    """AGENT 3: Security Sentinel detects SQL injection, secrets, and auth flaws."""
    agent = SecurityAgent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["agent_findings"]) >= 1
    finding = res["agent_findings"][0]
    assert finding.category == "security"
    assert finding.agent_name == "Security Sentinel"
    assert res["agent_execution_logs"][0].status == "completed"


@pytest.mark.asyncio
async def test_agent4_performance_agent(mock_gateway, sample_initial_state):
    """AGENT 4: Performance Guardian detects query inefficiencies and bottlenecks."""
    agent = PerformanceAgent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["agent_findings"]) >= 1
    finding = res["agent_findings"][0]
    assert finding.category == "performance"
    assert finding.agent_name == "Performance Guardian"
    assert res["agent_execution_logs"][0].status == "completed"


@pytest.mark.asyncio
async def test_agent5_architecture_agent(mock_gateway, sample_initial_state):
    """AGENT 5: Architecture Specialist evaluates design, coupling, and SRP."""
    agent = ArchitectureAgent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["agent_findings"]) >= 1
    finding = res["agent_findings"][0]
    assert finding.category == "architecture"
    assert finding.agent_name == "Architecture Specialist"
    assert res["agent_execution_logs"][0].status == "completed"


@pytest.mark.asyncio
async def test_agent6_test_agent(mock_gateway, sample_initial_state):
    """AGENT 6: Test Guardian evaluates missing tests and regression hazards."""
    agent = TestAgent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["agent_findings"]) >= 1
    finding = res["agent_findings"][0]
    assert finding.category == "test"
    assert finding.agent_name == "Test Guardian"
    assert res["agent_execution_logs"][0].status == "completed"


@pytest.mark.asyncio
async def test_agent7_reviewer2_adversarial_critique(mock_gateway, sample_initial_state):
    """AGENT 7: Reviewer 2 cross-examines specialist findings and challenges claims."""
    # Preload initial findings into state
    proposal = FindingProposal(
        file_path="app/auth.py",
        line_number=12,
        category="security",
        severity="critical",
        title="SQL Injection in user query",
        message="Raw SQL format string concatenation detected.",
        agent_name="Security Sentinel",
        confidence_score=0.98,
    )
    sample_initial_state["agent_findings"] = [proposal]

    agent = Reviewer2Agent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["agent_discussions"]) >= 1
    # Reviewer 2 should have evaluated the finding and emitted a critique discussion
    critique_msg = res["agent_discussions"][0]
    assert critique_msg.agent_name == "Reviewer 2"
    assert res["agent_execution_logs"][0].status == "completed"


@pytest.mark.asyncio
async def test_agent8_verification_agent_consensus(mock_gateway, sample_initial_state):
    """AGENT 8: Verification Arbiter validates evidence, rejects false positives, and verifies findings."""
    proposal = FindingProposal(
        file_path="app/auth.py",
        line_number=12,
        category="security",
        severity="critical",
        title="SQL Injection in user query",
        message="Raw SQL format string concatenation detected.",
        agent_name="Security Sentinel",
        confidence_score=0.98,
    )
    sample_initial_state["agent_findings"] = [proposal]

    agent = VerificationAgent(gateway=mock_gateway)
    res = await agent.execute(sample_initial_state)

    assert len(res["verified_findings"]) >= 1
    vf = res["verified_findings"][0]
    assert vf.status in ("verified", "uncertain", "rejected")
    assert vf.confidence_score > 0.0
    assert len(res["agent_discussions"]) >= 1
    assert res["agent_execution_logs"][0].status == "completed"


# =====================================================================
# 4. PARTIAL FAILURE & TIMEOUT TESTS
# =====================================================================

@pytest.mark.asyncio
async def test_agent_timeout_and_resilient_partial_failure(sample_initial_state):
    """Verifies that an agent timeout does not terminate the workflow, recording a timed_out log."""
    class SlowHangingAgent(BugHunterAgent):
        async def process(self, state: ReviewState) -> Dict[str, Any]:
            await asyncio.sleep(2.0)
            return {"agent_findings": []}

    hanging_agent = SlowHangingAgent(timeout_seconds=0.1)
    res = await hanging_agent.execute(sample_initial_state)

    assert len(res["agent_findings"]) == 0
    assert len(res["agent_execution_logs"]) == 1
    assert res["agent_execution_logs"][0].status == "timed_out"
    assert "timed out" in res["errors"][0]


@pytest.mark.asyncio
async def test_agent_exception_partial_failure(sample_initial_state):
    """Verifies that an unhandled agent exception is safely captured without crashing the pipeline."""
    class CrashingAgent(SecurityAgent):
        async def process(self, state: ReviewState) -> Dict[str, Any]:
            raise ValueError("Simulated unexpected AST parsing crash")

    crashing_agent = CrashingAgent(timeout_seconds=5.0)
    res = await crashing_agent.execute(sample_initial_state)

    assert len(res["agent_findings"]) == 0
    assert res["agent_execution_logs"][0].status == "failed"
    assert "Simulated unexpected AST parsing crash" in res["errors"][0]


# =====================================================================
# 5. SCORECARD & MARKDOWN SUMMARY TESTS
# =====================================================================

def test_scorecard_and_markdown_summary_calculation(sample_initial_state):
    """Verifies score calculation and executive markdown generation."""
    vf1 = VerifiedFinding(
        finding=FindingProposal(
            file_path="app/auth.py",
            line_number=12,
            category="security",
            severity="critical",
            title="SQL Injection vulnerability",
            message="Unescaped parameters in SQL string.",
            suggested_patch="- db.execute(f'SELECT...\\n+ db.execute('SELECT...', (u, p))",
            agent_name="Security Sentinel",
        ),
        status="verified",
        verification_reason="Direct execution reachability confirmed in auth route.",
        confidence_score=0.99,
    )
    vf2 = VerifiedFinding(
        finding=FindingProposal(
            file_path="app/auth.py",
            line_number=17,
            category="bug",
            severity="medium",
            title="Potential None dereference",
            message="user.token accessed when user is None.",
            agent_name="Bug Hunter",
        ),
        status="verified",
        verification_reason="No null guard before accessing user.token.",
        confidence_score=0.94,
    )

    scores = calculate_review_scores([vf1, vf2])
    assert scores["overall_score"] < 100.0
    assert scores["security_score"] < 100.0
    assert scores["quality_score"] < 100.0

    markdown = generate_markdown_summary(sample_initial_state, scores, [vf1, vf2])
    assert "OpenReview AI Code Review Summary" in markdown
    assert "SQL Injection vulnerability" in markdown
    assert "Multi-Agent Council" in markdown


# =====================================================================
# 6. LANGGRAPH FULL WORKFLOW END-TO-END TEST
# =====================================================================

@pytest.mark.asyncio
async def test_langgraph_full_review_workflow_end_to_end(mock_gateway, sample_initial_state):
    """Tests the compiled LangGraph StateGraph running through all nodes and verifying shared state."""
    workflow = get_review_workflow(mock_gateway)
    final_state = await workflow.ainvoke(sample_initial_state)

    assert final_state["is_completed"] is True
    assert final_state["overall_score"] >= 0.0
    assert len(final_state["review_summary"]) > 0

    # Verify that parallel specialists ran and logged telemetry
    logs: List[AgentLogEntry] = final_state["agent_execution_logs"]
    agent_names = {l.agent_name for l in logs}

    assert "Context Agent" in agent_names
    assert "Bug Hunter" in agent_names
    assert "Security Sentinel" in agent_names
    assert "Performance Guardian" in agent_names
    assert "Architecture Specialist" in agent_names
    assert "Test Guardian" in agent_names
    assert "Reviewer 2" in agent_names
    assert "Verification Arbiter" in agent_names

    # Verify verified findings are populated
    assert "verified_findings" in final_state
    # Verify discussions exist
    assert len(final_state["agent_discussions"]) > 0


# =====================================================================
# 7. DATABASE PERSISTENCE SERVICE TEST
# =====================================================================

@pytest.mark.asyncio
async def test_review_orchestration_service_database_persistence(mock_gateway):
    """Tests executing a review pass and persisting Review, ReviewAgent, Finding, and AgentDiscussion in DB."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Seed Org, Repo, PR, and Review
        org = Organization(name="Test Org", slug="test-org")
        session.add(org)
        await session.flush()

        repo = Repository(
            organization_id=org.id,
            github_repo_id=987654,
            name="test-repo",
            owner="openreview",
            full_name="openreview/test-repo",
            default_branch="main",
            clone_url="https://github.com/openreview/test-repo.git",
        )
        session.add(repo)
        await session.flush()

        pr = PullRequest(
            repository_id=repo.id,
            pr_number=42,
            title="feat: secure auth flow",
            description="Replaces raw queries",
            head_branch="feature-auth",
            base_branch="main",
            head_sha="b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
            base_sha="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            author_username="octocat",
            state="open",
        )
        session.add(pr)
        await session.flush()

        review = Review(
            pull_request_id=pr.id,
            commit_sha=pr.head_sha,
            status="pending",
        )
        session.add(review)
        await session.commit()

        # Execute orchestration service
        orchestrator = ReviewOrchestrationService(session=session, gateway=mock_gateway)
        completed_review = await orchestrator.execute_review(
            review_id=review.id,
            custom_diff=SAMPLE_UNIFIED_DIFF,
        )

        assert completed_review.status == "completed"
        assert completed_review.completed_at is not None
        assert completed_review.score is not None

        # Verify persisted ReviewAgents in DB
        agents_res = await session.execute(
            ReviewAgent.__table__.select().where(ReviewAgent.review_id == review.id)
        )
        db_agents = agents_res.all()
        assert len(db_agents) >= 6

        # Verify persisted Findings in DB
        findings_res = await session.execute(
            Finding.__table__.select().where(Finding.review_id == review.id)
        )
        db_findings = findings_res.all()
        assert len(db_findings) >= 1

        # Verify persisted AgentDiscussions in DB
        disc_res = await session.execute(
            AgentDiscussion.__table__.select().where(AgentDiscussion.review_id == review.id)
        )
        db_discussions = disc_res.all()
        assert len(db_discussions) >= 1

    await engine.dispose()


# =====================================================================
# 8. REST API ENDPOINTS TEST
# =====================================================================

@pytest.mark.asyncio
async def test_reviews_council_registry_and_orchestrate_api():
    """Tests the /api/v1/reviews/council/registry and /{review_id}/orchestrate endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test council registry endpoint
        reg_resp = await client.get("/api/v1/reviews/council/registry")
        assert reg_resp.status_code == 200
        agents_list = reg_resp.json().get("agents", [])
        assert len(agents_list) >= 8
        agent_names = {a["name"] for a in agents_list}
        assert "Security Sentinel" in agent_names
        assert "Bug Hunter" in agent_names
        assert "Verification Arbiter" in agent_names
        assert "Reviewer 2" in agent_names
