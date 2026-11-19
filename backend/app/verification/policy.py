"""Configurable Review Policy Engine.

Evaluates verified findings against team/repository publishing policies
to ensure only high-quality, actionable, and substantiated comments are posted.
"""

from typing import Dict, Optional, Tuple
from app.verification.schemas import (
    FindingSeverity,
    ReviewPolicyConfig,
    VerificationStatus,
    VerifiedFinding,
)

SEVERITY_RANKS: Dict[FindingSeverity, int] = {
    FindingSeverity.INFORMATIONAL: 0,
    FindingSeverity.LOW: 1,
    FindingSeverity.MEDIUM: 2,
    FindingSeverity.HIGH: 3,
    FindingSeverity.CRITICAL: 4,
}


class PolicyDecision:
    """Decision outcome of applying a review policy to a verified finding."""

    def __init__(self, is_publishable: bool, reason: str, policy_name: str):
        self.is_publishable = is_publishable
        self.reason = reason
        self.policy_name = policy_name

    def __repr__(self) -> str:
        return f"<PolicyDecision publishable={self.is_publishable} reason='{self.reason}'>"


class ReviewPolicyEngine:
    """Evaluates verified findings against configurable thresholds."""

    @staticmethod
    def get_standard_policy() -> ReviewPolicyConfig:
        """Balanced production policy: Confirmed & High-confidence issues."""
        return ReviewPolicyConfig(
            policy_name="Standard Production Policy",
            min_confidence=0.70,
            allowed_statuses=[
                VerificationStatus.CONFIRMED,
                VerificationStatus.HIGH_CONFIDENCE,
            ],
            min_severity=FindingSeverity.LOW,
            block_duplicates=True,
            require_source_evidence=True,
            require_remediation=True,
            min_actionability=0.60,
        )

    @staticmethod
    def get_strict_policy() -> ReviewPolicyConfig:
        """High-assurance policy: Only 100% verified findings with executable patches."""
        return ReviewPolicyConfig(
            policy_name="Strict High-Assurance Policy",
            min_confidence=0.85,
            allowed_statuses=[VerificationStatus.CONFIRMED],
            min_severity=FindingSeverity.MEDIUM,
            block_duplicates=True,
            require_source_evidence=True,
            require_remediation=True,
            min_actionability=0.75,
        )

    @staticmethod
    def get_security_only_policy() -> ReviewPolicyConfig:
        """Security audit policy: Only High & Critical security vulnerabilities."""
        return ReviewPolicyConfig(
            policy_name="Security-Only Audit Policy",
            min_confidence=0.80,
            allowed_statuses=[
                VerificationStatus.CONFIRMED,
                VerificationStatus.HIGH_CONFIDENCE,
            ],
            min_severity=FindingSeverity.HIGH,
            block_duplicates=True,
            require_source_evidence=True,
            require_remediation=True,
            min_actionability=0.50,
            allowed_categories=["security"],
        )

    @staticmethod
    def get_permissive_policy() -> ReviewPolicyConfig:
        """Development & exploratory policy: Includes warnings and investigations."""
        return ReviewPolicyConfig(
            policy_name="Permissive Development Policy",
            min_confidence=0.40,
            allowed_statuses=[
                VerificationStatus.CONFIRMED,
                VerificationStatus.HIGH_CONFIDENCE,
                VerificationStatus.NEEDS_INVESTIGATION,
            ],
            min_severity=FindingSeverity.INFORMATIONAL,
            block_duplicates=False,
            require_source_evidence=False,
            require_remediation=False,
            min_actionability=0.30,
        )

    @classmethod
    def evaluate(
        cls,
        finding: VerifiedFinding,
        policy: Optional[ReviewPolicyConfig] = None,
    ) -> PolicyDecision:
        """Evaluates whether a verified finding satisfies the given policy."""
        active_policy = policy or cls.get_standard_policy()

        # 1. Hard Rejection Check
        if finding.verification_status == VerificationStatus.REJECTED:
            return PolicyDecision(
                is_publishable=False,
                reason=f"Filtered: Finding was rejected during verification ({finding.rejection_reason or 'unsubstantiated'}).",
                policy_name=active_policy.policy_name,
            )

        # 2. Duplicate Check
        if active_policy.block_duplicates and finding.duplicate_of_id:
            return PolicyDecision(
                is_publishable=False,
                reason=f"Filtered: Redundant duplicate of primary finding #{finding.duplicate_of_id}.",
                policy_name=active_policy.policy_name,
            )

        # 3. Status Check
        if finding.verification_status not in active_policy.allowed_statuses:
            return PolicyDecision(
                is_publishable=False,
                reason=f"Filtered: Status '{finding.verification_status.value}' is not permitted by policy (requires one of {[s.value for s in active_policy.allowed_statuses]}).",
                policy_name=active_policy.policy_name,
            )

        # 4. Confidence Threshold Check (strictly separate from severity)
        if finding.confidence < active_policy.min_confidence:
            return PolicyDecision(
                is_publishable=False,
                reason=f"Filtered: Calibrated confidence ({finding.confidence:.2f}) is below minimum policy threshold ({active_policy.min_confidence:.2f}).",
                policy_name=active_policy.policy_name,
            )

        # 5. Category Filter
        if active_policy.allowed_categories is not None:
            if finding.category.lower() not in [c.lower() for c in active_policy.allowed_categories]:
                return PolicyDecision(
                    is_publishable=False,
                    reason=f"Filtered: Category '{finding.category}' is not in policy allowed categories: {active_policy.allowed_categories}.",
                    policy_name=active_policy.policy_name,
                )

        # 6. Severity Threshold Check
        finding_rank = SEVERITY_RANKS.get(finding.severity, 1)
        required_rank = SEVERITY_RANKS.get(active_policy.min_severity, 1)
        if finding_rank < required_rank:
            return PolicyDecision(
                is_publishable=False,
                reason=f"Filtered: Severity '{finding.severity.value}' is lower than policy minimum '{active_policy.min_severity.value}'.",
                policy_name=active_policy.policy_name,
            )

        # 7. Source Evidence Requirement
        if active_policy.require_source_evidence and (
            not finding.source_evidence or not finding.source_evidence.strip()
        ):
            return PolicyDecision(
                is_publishable=False,
                reason="Filtered: Policy mandates concrete source code evidence snippet.",
                policy_name=active_policy.policy_name,
            )

        # 8. Actionability & Remediation Requirement
        if active_policy.require_remediation and (
            not finding.suggested_remediation or not finding.suggested_remediation.strip()
        ):
            return PolicyDecision(
                is_publishable=False,
                reason="Filtered: Policy mandates actionable suggested remediation instructions or patch.",
                policy_name=active_policy.policy_name,
            )

        if finding.actionability_score < active_policy.min_actionability:
            return PolicyDecision(
                is_publishable=False,
                reason=f"Filtered: Actionability score ({finding.actionability_score:.2f}) is below policy threshold ({active_policy.min_actionability:.2f}).",
                policy_name=active_policy.policy_name,
            )

        # All checks passed!
        return PolicyDecision(
            is_publishable=True,
            reason=f"Approved: Satisfies '{active_policy.policy_name}' ({finding.verification_status.value}, confidence {finding.confidence:.2f}, severity {finding.severity.value}).",
            policy_name=active_policy.policy_name,
        )
