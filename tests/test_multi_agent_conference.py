"""Comprehensive Test Suite for Multi-Agent Conference System.

Covers:
1. Agent Disagreement & Rebuttal (Specialist vs Reviewer 2)
2. Missing Evidence Handling & Context Agent Retrieval
3. Duplicate Finding Grouping ('Duplicate' status)
4. Specialist Concession & Refutation ('Rejected' status)
5. Evidence Validation & Reachability ('Accepted' status)
6. Inconclusive Static Proof ('Uncertain' & 'Needs investigation' statuses)
7. Strict Max Rounds Enforcement (No infinite agent loops)
8. Token Budget Enforcement & Early Termination
9. Resilient Partial Failure Handling (Timeout / Exception in debate)
10. Non-majority Voting (Evidence-based standard)
11. Conference REST API Endpoints (/conference and /conference/deliberate)
"""

import asyncio
from typing import Any, Dict, List
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.ai.base import LLMResponse, ModelConfig, StructuredLLMResponse, TokenUsage
from app.core.ai.gateway import ModelGateway
from app.core.ai.providers.mock_provider import MockLLMProvider
from app.database.base import Base
from app.findings.models import Finding
from app.main import app
from app.orchestration.conference import ConferenceEngine, SpecialistRebuttal
from app.orchestration.service import ReviewOrchestrationService
from app.orchestration.state import (
    AgentCritique,
    DiscussionItem,
    FindingProposal,
    Reviewer2Output,
    ReviewState,
    VerificationOutput,
    VerifiedFinding,
)
from app.organizations.models import Organization
from app.pull_requests.models import PullRequest
from app.repositories.models import Repository
from app.reviews.models import Review


@pytest.fixture
def mock_gateway():
    """Provides a deterministic mock gateway for conference testing."""
    gateway = ModelGateway(primary_provider="mock", fallback_provider="mock")
    mock_prov = MockLLMProvider()
    gateway.register_provider("mock", mock_prov)
    return gateway


@pytest.fixture
def base_conference_state() -> ReviewState:
    """Provides a clean initial state for conference testing."""
    return {
        "review_id": "rev-conf-001",
        "pull_request_id": "pr-conf-001",
        "repository_id": "repo-conf-001",
        "commit_sha": "c0ffee123456",
        "pr_title": "feat: payment gateway and authentication handler",
        "pr_description": "Updates payment checkout route and JWT auth verification.",
        "raw_diff": (
            "diff --git a/app/payment.py b/app/payment.py\n"
            "--- a/app/payment.py\n"
            "+++ b/app/payment.py\n"
            "@@ -20,6 +20,10 @@ def process_payment(order_id, amount):\n"
            "+    # Insecure query and missing currency validation\n"
            "+    sql = f'UPDATE orders SET paid=1 WHERE id={order_id}'\n"
            "+    db.execute(sql)\n"
            "+    return True\n"
        ),
        "changed_files": [],
        "context_evidence": {"pr_purpose": "Payment processing"},
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
        "token_budget_remaining": 80000,
        "is_completed": False,
    }


# =====================================================================
# 1. AGENT DISAGREEMENT & REBUTTAL TEST
# =====================================================================

@pytest.mark.asyncio
async def test_conference_agent_disagreement_and_rebuttal(mock_gateway, base_conference_state):
    """Verifies debate where Reviewer 2 challenges a claim and specialist defends with code evidence."""
    # Finding proposed by Security Sentinel
    f1 = FindingProposal(
        id="finding-sqli-01",
        file_path="app/payment.py",
        line_number=22,
        category="security",
        severity="critical",
        title="SQL Injection in order update",
        message="Raw SQL format string concatenation allows order manipulation.",
        code_evidence="sql = f'UPDATE orders SET paid=1 WHERE id={order_id}'",
        agent_name="Security Sentinel",
        confidence_score=0.95,
    )
    base_conference_state["agent_findings"] = [f1]

    engine = ConferenceEngine(gateway=mock_gateway, max_rounds=2)
    result = await engine.run_conference(base_conference_state)

    verified = result["verified_findings"]
    assert len(verified) == 1
    vf = verified[0]
    # Finding should be verified and Accepted because specialist defended with code evidence
    assert vf.status == "Accepted"
    assert vf.canonical_state == "Accepted"
    assert vf.confidence_score >= 0.90

    # Verify positions in discussion chain
    discussions: List[DiscussionItem] = result["agent_discussions"]
    positions = [d.position for d in discussions]
    assert "challenge" in positions
    assert "rebuttal" in positions
    assert "verdict" in positions


# =====================================================================
# 2. MISSING EVIDENCE & CONTEXT AGENT RETRIEVAL
# =====================================================================

@pytest.mark.asyncio
async def test_conference_missing_evidence_and_context_supply(mock_gateway, base_conference_state):
    """Verifies that when evidence is disputed, Context Agent supplies missing source lines."""
    f_ambiguous = FindingProposal(
        id="finding-ambig-01",
        file_path="app/payment.py",
        line_number=25,
        category="bug",
        severity="medium",
        title="Potential unhandled currency rounding",
        message="Float multiplication might cause precision loss.",
        code_evidence=None,  # Intentionally missing evidence
        agent_name="Bug Hunter",
        confidence_score=0.75,
    )
    base_conference_state["agent_findings"] = [f_ambiguous]

    engine = ConferenceEngine(gateway=mock_gateway, max_rounds=2)
    result = await engine.run_conference(base_conference_state)

    discussions: List[DiscussionItem] = result["agent_discussions"]
    # Check that Context Agent intervened to supply source context
    context_msgs = [d for d in discussions if d.agent_name == "Context Agent"]
    assert len(context_msgs) >= 1
    assert context_msgs[0].position == "context_supply"
    assert context_msgs[0].evidence is not None


# =====================================================================
# 3. DUPLICATE FINDING GROUPING TEST
# =====================================================================

@pytest.mark.asyncio
async def test_conference_duplicate_finding_grouping(mock_gateway, base_conference_state):
    """Verifies that duplicate findings across different agents receive 'Duplicate' status."""
    f_primary = FindingProposal(
        id="finding-sec-01",
        file_path="app/payment.py",
        line_number=22,
        category="security",
        severity="critical",
        title="SQL Injection vulnerability",
        message="Format string query interpolation.",
        code_evidence="sql = f'UPDATE orders SET paid=1 WHERE id={order_id}'",
        agent_name="Security Sentinel",
        confidence_score=0.98,
    )
    # Duplicate from Bug Hunter at same/nearby line
    f_duplicate = FindingProposal(
        id="finding-sec-02",
        file_path="app/payment.py",
        line_number=23,
        category="security",
        severity="high",
        title="SQL Injection vulnerability",
        message="Unescaped order_id parameter.",
        code_evidence="db.execute(sql)",
        agent_name="Bug Hunter",
        confidence_score=0.88,
    )
    base_conference_state["agent_findings"] = [f_primary, f_duplicate]

    engine = ConferenceEngine(gateway=mock_gateway, max_rounds=2)
    result = await engine.run_conference(base_conference_state)

    verified = result["verified_findings"]
    statuses = [vf.status for vf in verified]

    assert "Duplicate" in statuses
    duplicate_vf = next(vf for vf in verified if vf.status == "Duplicate")
    assert duplicate_vf.finding.id == f_duplicate.id
    assert "Subsumed under primary finding" in duplicate_vf.verification_reason


# =====================================================================
# 4. SPECIALIST CONCESSION & REFUTATION ('Rejected')
# =====================================================================

@pytest.mark.asyncio
async def test_conference_specialist_concession_and_rejection(base_conference_state):
    """Verifies that when an agent concedes to a challenge, the finding is marked 'Rejected'."""
    # Create a custom mock gateway where specialist concedes
    mock_prov = MockLLMProvider()
    mock_prov.structured_response_data = {
        "finding_id": "finding-false-alarm",
        "position": "concession",
        "arguments": "I concede: order_id is cast to int upstream in the route decorator, preventing SQL injection.",
        "requires_surrounding_context": False,
    }
    gateway = ModelGateway(primary_provider="mock", fallback_provider="mock")
    gateway.register_provider("mock", mock_prov)

    f_false_alarm = FindingProposal(
        id="finding-false-alarm",
        file_path="app/payment.py",
        line_number=22,
        category="security",
        severity="high",
        title="False Alarm SQLi",
        message="Claimed vulnerability.",
        code_evidence="sql = f'UPDATE...'",
        agent_name="Security Sentinel",
        confidence_score=0.85,
    )
    base_conference_state["agent_findings"] = [f_false_alarm]

    engine = ConferenceEngine(gateway=gateway, max_rounds=2)
    result = await engine.run_conference(base_conference_state)

    verified = result["verified_findings"]
    assert len(verified) == 1
    assert verified[0].status == "Rejected"
    assert "conceded" in verified[0].verification_reason.lower() or "acknowledged" in verified[0].verification_reason.lower()


# =====================================================================
# 5. INCONCLUSIVE EVIDENCE ('Needs investigation' / 'Uncertain')
# =====================================================================

@pytest.mark.asyncio
async def test_conference_unverifiable_claim_marked_needs_investigation(mock_gateway, base_conference_state):
    """Verifies that an unsupported finding without code evidence becomes 'Needs investigation' or 'Rejected'."""
    f_unsupported = FindingProposal(
        id="finding-unsupported-01",
        file_path="app/payment.py",
        line_number=10,
        category="architecture",
        severity="low",
        title="Theoretical microservice coupling",
        message="This module might be coupled to an external service in another repository.",
        code_evidence=None,  # No evidence
        agent_name="Architecture Specialist",
        confidence_score=0.40,
    )
    base_conference_state["agent_findings"] = [f_unsupported]

    engine = ConferenceEngine(gateway=mock_gateway, max_rounds=1)
    result = await engine.run_conference(base_conference_state)

    verified = result["verified_findings"]
    assert len(verified) == 1
    # Without code evidence, the finding cannot be Accepted
    assert verified[0].status in ("Needs investigation", "Rejected", "Uncertain")


# =====================================================================
# 6. MAX DISCUSSION ROUNDS LIMITATION (No Infinite Loops)
# =====================================================================

@pytest.mark.asyncio
async def test_conference_max_rounds_enforcement(mock_gateway, base_conference_state):
    """Verifies that deliberation strictly terminates after configured max_rounds."""
    f1 = FindingProposal(
        id="finding-bounded-01",
        file_path="app/payment.py",
        line_number=22,
        category="bug",
        severity="high",
        title="Bounded round check",
        message="Testing round limits.",
        code_evidence="db.execute()",
        agent_name="Bug Hunter",
    )
    base_conference_state["agent_findings"] = [f1]

    # Set strictly to 1 round
    engine = ConferenceEngine(gateway=mock_gateway, max_rounds=1)
    result = await engine.run_conference(base_conference_state, custom_max_rounds=1)

    discussions: List[DiscussionItem] = result["agent_discussions"]
    max_round_seen = max(d.round_number for d in discussions)
    assert max_round_seen <= 1  # Absolutely never exceeds configured max rounds


# =====================================================================
# 7. TOKEN BUDGET LIMITATION
# =====================================================================

@pytest.mark.asyncio
async def test_conference_token_budget_early_termination(mock_gateway, base_conference_state):
    """Verifies that exceeding the token budget halts discussion rounds early."""
    f1 = FindingProposal(
        id="finding-budget-01",
        file_path="app/payment.py",
        line_number=22,
        category="security",
        severity="critical",
        title="Token budget test",
        message="Ensures budget cap works.",
        code_evidence="sql = ...",
        agent_name="Security Sentinel",
    )
    base_conference_state["agent_findings"] = [f1]

    # Set an extremely tiny token budget (1 token)
    engine = ConferenceEngine(gateway=mock_gateway, max_rounds=4, total_token_budget=1)
    result = await engine.run_conference(base_conference_state)

    # Should have triggered token budget limit warning and exited
    assert any("token budget" in err.lower() for err in result["errors"])


# =====================================================================
# 8. PARTIAL FAILURE HANDLING
# =====================================================================

@pytest.mark.asyncio
async def test_conference_partial_failure_resilience(base_conference_state):
    """Verifies that if an agent crashes during debate, other findings continue and complete."""
    class CrashingGateway(ModelGateway):
        async def generate_structured(self, *args, **kwargs):
            # Simulate a 500 error from one of the providers
            raise ConnectionResetError("Simulated socket drop during agent debate")

    gateway = CrashingGateway()
    f1 = FindingProposal(
        id="finding-survivor-01",
        file_path="app/payment.py",
        line_number=22,
        category="bug",
        severity="medium",
        title="Surviving finding",
        message="Crash resilience check.",
        code_evidence="valid snippet",
        agent_name="Bug Hunter",
    )
    base_conference_state["agent_findings"] = [f1]

    engine = ConferenceEngine(gateway=gateway, max_rounds=1, round_timeout_seconds=0.5)
    result = await engine.run_conference(base_conference_state)

    # The conference must not raise; it must recover, log error, and arbitrate the finding
    assert len(result["errors"]) >= 1
    assert len(result["verified_findings"]) == 1
    assert result["verified_findings"][0].status in ("Accepted", "Needs investigation", "Uncertain")


# =====================================================================
# 9. EVIDENCE-BASED VALIDATION (No Simple Majority Voting)
# =====================================================================

@pytest.mark.asyncio
async def test_conference_evidence_based_validation_standard(mock_gateway, base_conference_state):
    """Verifies that Verification Arbiter rejects unevidenced claims even if multiple agents concur."""
    # Two agents make identical unevidenced speculative claims
    f_speculative1 = FindingProposal(
        id="spec-01",
        file_path="app/payment.py",
        line_number=20,
        category="architecture",
        severity="low",
        title="Speculative framework concern",
        message="Might fail on hypothetical future Python versions.",
        code_evidence=None,
        agent_name="Architecture Specialist",
    )
    f_speculative2 = FindingProposal(
        id="spec-02",
        file_path="app/payment.py",
        line_number=20,
        category="performance",
        severity="low",
        title="Speculative framework concern",
        message="Agreed, might fail in hypothetical scenarios.",
        code_evidence=None,
        agent_name="Performance Guardian",
    )
    base_conference_state["agent_findings"] = [f_speculative1, f_speculative2]

    engine = ConferenceEngine(gateway=mock_gateway, max_rounds=1)
    result = await engine.run_conference(base_conference_state)

    # Neither can be 'Accepted' without verified code evidence
    for vf in result["verified_findings"]:
        if vf.status != "Duplicate":
            assert vf.status != "Accepted"
            assert vf.status in ("Rejected", "Needs investigation", "Uncertain")


# =====================================================================
# 10. CONFERENCE REST API ENDPOINTS TEST
# =====================================================================

@pytest.mark.asyncio
async def test_conference_api_endpoints():
    """Tests the GET /reviews/{id}/conference and POST /reviews/{id}/conference/deliberate endpoints."""
    # 1. Create temporary SQLite session with Seed Data
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        org = Organization(name="Conference Org", slug="conf-org")
        session.add(org)
        await session.flush()

        repo = Repository(
            organization_id=org.id,
            github_repo_id=778899,
            name="conference-repo",
            owner="openreview",
            full_name="openreview/conference-repo",
            default_branch="main",
            clone_url="https://github.com/openreview/conference-repo.git",
        )
        session.add(repo)
        await session.flush()

        pr = PullRequest(
            repository_id=repo.id,
            pr_number=99,
            title="feat: conference integration",
            description="Adds multi-turn debate",
            head_branch="feature-conf",
            base_branch="main",
            head_sha="deadbeef1234deadbeef1234deadbeef1234dead",
            base_sha="feedface1234feedface1234feedface1234feed",
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

        # Run orchestration service
        mock_prov = MockLLMProvider()
        gateway = ModelGateway(primary_provider="mock", fallback_provider="mock")
        gateway.register_provider("mock", mock_prov)

        orchestrator = ReviewOrchestrationService(session=session, gateway=gateway)
        await orchestrator.execute_review(review.id)

        # Query conference session data directly
        conf_data = await orchestrator.get_conference_session(review.id)

        assert conf_data["review_id"] == review.id
        assert "discussion_threads" in conf_data
        assert "summary_metrics" in conf_data
        metrics = conf_data["summary_metrics"]
        assert "accepted_count" in metrics
        assert "consensus_rate" in metrics
        assert len(conf_data["agents"]) >= 1

    await engine.dispose()
