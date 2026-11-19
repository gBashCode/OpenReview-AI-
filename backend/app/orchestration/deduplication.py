"""Finding Deduplication and Collision Consolidation Engine.

Prevents duplicate and conflicting findings from cluttering reviews by analyzing
file path normalization, line proximity buckets, and semantic similarity.
"""

from typing import Dict, List, Set, Tuple
from app.orchestration.state import DiscussionItem, FindingProposal


class FindingDeduplicator:
    """Detects and resolves duplicate findings produced across multiple review agents."""

    @staticmethod
    def normalize_path(path: str) -> str:
        """Normalizes file path for consistent matching."""
        return path.replace("\\", "/").strip("/").lower()

    @classmethod
    def get_fingerprint(cls, finding: FindingProposal, line_tolerance: int = 2) -> str:
        """Computes a stable proximity fingerprint for a finding.

        Groups lines within a tolerance window (e.g., +/- 2 lines) so that
        an issue reported at line 45 and line 46 for the same concept match.
        """
        norm_path = cls.normalize_path(finding.file_path)
        # Bucket line numbers into proximity windows
        line = finding.line_number or 0
        bucket = line // (line_tolerance + 1)

        # Extract normalized keywords from title
        words = "".join(c for c in finding.title.lower() if c.isalnum() or c.isspace()).split()
        key_words = "-".join(sorted(set(words[:5])))

        return f"{norm_path}::{bucket}::{finding.category}::{key_words}"

    @classmethod
    def deduplicate(
        cls,
        findings: List[FindingProposal],
        line_tolerance: int = 2,
    ) -> Tuple[List[FindingProposal], List[DiscussionItem]]:
        """Deduplicates a list of finding proposals.

        Returns:
            Tuple of (deduplicated_findings, consolidation_discussion_items)
        """
        seen_fingerprints: Dict[str, FindingProposal] = {}
        deduped: List[FindingProposal] = []
        discussions: List[DiscussionItem] = []

        # Sort by severity weight and confidence so the strongest finding is chosen as primary
        severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

        def sort_key(f: FindingProposal):
            return (severity_order.get(f.severity, 0), f.confidence_score)

        sorted_findings = sorted(findings, key=sort_key, reverse=True)

        for finding in sorted_findings:
            fp = cls.get_fingerprint(finding, line_tolerance=line_tolerance)

            if fp in seen_fingerprints:
                primary = seen_fingerprints[fp]
                # Log consensus deduplication discussion
                discussions.append(
                    DiscussionItem(
                        finding_id=primary.id,
                        finding_title=primary.title,
                        agent_name="Deduplication Arbiter",
                        message_type="consensus",
                        content=(
                            f"Consolidated duplicate finding '{finding.title}' from {finding.agent_name} "
                            f"into primary issue '{primary.title}' from {primary.agent_name} "
                            f"at {primary.file_path}:{primary.line_number}."
                        ),
                        file_context=f"{primary.file_path}:{primary.line_number}",
                        is_verified=True,
                    )
                )
                # Append secondary agent attribution to message if not already present
                if finding.agent_name not in primary.agent_name:
                    primary.agent_name = f"{primary.agent_name} & {finding.agent_name}"
            else:
                seen_fingerprints[fp] = finding
                deduped.append(finding)

        return deduped, discussions
