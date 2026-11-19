"""Finding Verification Application Service.

Coordinates verification workflows, review analysis validation, and database updates.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.findings.models import Finding
from app.reviews.models import Review
from app.verification.engine import FindingVerificationEngine
from app.verification.policy import ReviewPolicyEngine
from app.verification.schemas import (
    CandidateFinding,
    FindingSeverity,
    ReviewPolicyConfig,
    VerificationBatchResult,
    VerificationStatus,
    VerifiedFinding,
)

logger = get_logger("openreview.verification.service")


class FindingVerificationService:
    """Manages finding verification lifecycles and persistence."""

    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.engine = FindingVerificationEngine()

    def verify_candidate(
        self,
        candidate: CandidateFinding,
        repository_files: Optional[Dict[str, str]] = None,
        changed_files: Optional[List[Dict[str, Any]]] = None,
        test_files: Optional[List[str]] = None,
        context_evidence: Optional[Dict[str, Any]] = None,
        policy: Optional[ReviewPolicyConfig] = None,
    ) -> VerifiedFinding:
        """Verifies a single candidate finding."""
        if policy:
            engine = FindingVerificationEngine(policy=policy)
        else:
            engine = self.engine

        return engine.verify_finding(
            candidate=candidate,
            repository_files=repository_files,
            changed_files=changed_files,
            test_files=test_files,
            context_evidence=context_evidence,
        )

    def verify_candidates_batch(
        self,
        candidates: List[CandidateFinding],
        repository_files: Optional[Dict[str, str]] = None,
        changed_files: Optional[List[Dict[str, Any]]] = None,
        test_files: Optional[List[str]] = None,
        context_evidence: Optional[Dict[str, Any]] = None,
        policy: Optional[ReviewPolicyConfig] = None,
    ) -> VerificationBatchResult:
        """Verifies a batch of candidates with duplicate suppression."""
        active_policy = policy or ReviewPolicyEngine.get_standard_policy()
        engine = FindingVerificationEngine(policy=active_policy)
        return engine.verify_batch(
            candidates=candidates,
            repository_files=repository_files,
            changed_files=changed_files,
            test_files=test_files,
            context_evidence=context_evidence,
            policy=active_policy,
        )

    async def verify_review_findings(
        self,
        review_id: str,
        policy: Optional[ReviewPolicyConfig] = None,
    ) -> VerificationBatchResult:
        """Loads findings for a review from the database, validates them, and persists outcomes."""
        if not self.session:
            raise ValueError("AsyncSession required for verify_review_findings.")

        stmt = (
            select(Review)
            .options(
                selectinload(Review.findings),
                selectinload(Review.pull_request),
            )
            .where(Review.id == review_id)
        )
        review = (await self.session.execute(stmt)).scalar_one_or_none()
        if not review:
            raise NotFoundError("Review", review_id)

        # Convert ORM findings to CandidateFindings
        candidates: List[CandidateFinding] = []
        for f in review.findings:
            candidates.append(
                CandidateFinding(
                    id=f.id,
                    title=f.title,
                    description=f.message,
                    file_path=f.file_path,
                    start_line=f.line_number,
                    end_line=f.end_line_number,
                    severity=f.severity,
                    confidence=f.confidence_score or 0.8,
                    source_evidence=f.evidence,
                    suggested_remediation=f.suggested_patch,
                    category=f.category,
                    agent_name=f.agent_name,
                )
            )

        batch_result = self.verify_candidates_batch(
            candidates=candidates,
            policy=policy,
        )

        # Update ORM models with verified metadata
        verified_map = {vf.id: vf for vf in batch_result.verified_findings}
        for f in review.findings:
            vf = verified_map.get(f.id)
            if vf:
                f.confidence_score = vf.confidence
                if hasattr(f, "verification_status"):
                    f.verification_status = vf.verification_status.value
                if hasattr(f, "root_cause"):
                    f.root_cause = vf.root_cause
                if hasattr(f, "impact"):
                    f.impact = vf.impact
                if hasattr(f, "actionability_score"):
                    f.actionability_score = vf.actionability_score
                if hasattr(f, "is_publishable"):
                    f.is_publishable = vf.is_publishable
                if hasattr(f, "rejection_reason"):
                    f.rejection_reason = vf.rejection_reason

        await self.session.commit()
        return batch_result
