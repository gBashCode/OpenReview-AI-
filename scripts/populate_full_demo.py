import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.database.session import AsyncSessionLocal
from app.models import *
from sqlalchemy import select


async def populate():
    async with AsyncSessionLocal() as session:
        # Find latest review
        reviews = (await session.execute(select(Review).order_by(Review.created_at.desc()))).scalars().all()
        if not reviews:
            print("No reviews found. Run scripts/seed_demo_data.py first.")
            return

        latest_review = reviews[0]
        print(f"Populating findings and discussions for Review: {latest_review.id} (Status: {latest_review.status})")

        # Create findings
        f1 = Finding(
            review_id=latest_review.id,
            file_path="backend/app/demo_sample.py",
            line_number=9,
            end_line_number=9,
            side="RIGHT",
            category="bug",
            severity="high",
            title="Unhandled Empty List or NoneType causes ZeroDivisionError",
            message="Calling `calculate_average(values)` with an empty list or None raises ZeroDivisionError or TypeError on `sum(values) / len(values)`.",
            suggested_patch="```python\n    if not values:\n        return 0.0\n    return float(sum(values)) / len(values)\n```",
            agent_name="Bug Hunter",
            confidence_score=0.96,
            discussion_state="Accepted",
            verification_status="Confirmed",
            root_cause="Missing guard check against empty collection or None value before division.",
            impact="Unhandled 500 runtime error crashing request handlers processing empty dataset queries.",
            actionability_score=0.95,
            is_publishable=True,
            is_resolved=False,
        )

        f2 = Finding(
            review_id=latest_review.id,
            file_path="backend/app/demo_sample.py",
            line_number=13,
            end_line_number=13,
            side="RIGHT",
            category="security",
            severity="critical",
            title="Potential SQL Injection in Raw Table Interpolation",
            message="Dynamic string interpolation `f'SELECT * FROM {table_name}'` allows SQL injection if table_name is user-controlled.",
            suggested_patch="```python\n    # Validate table against whitelist\n    ALLOWED_TABLES = {'users', 'transactions', 'audits'}\n    if table_name not in ALLOWED_TABLES:\n        raise ValueError(f'Invalid table identifier: {table_name}')\n```",
            agent_name="Security Agent",
            confidence_score=0.98,
            discussion_state="Accepted",
            verification_status="Confirmed",
            root_cause="Unsanitized string interpolation directly into dynamic SQL query statement.",
            impact="Unauthorized table access, data exfiltration, or table modification by malicious actors.",
            actionability_score=0.99,
            is_publishable=True,
            is_resolved=False,
        )

        f3 = Finding(
            review_id=latest_review.id,
            file_path="backend/app/demo_sample.py",
            line_number=8,
            end_line_number=9,
            side="RIGHT",
            category="performance",
            severity="medium",
            title="Repeated List Iteration in Mean Computation",
            message="`sum(values)` and `len(values)` both iterate or inspect elements; consider single-pass generator for large datasets.",
            agent_name="Performance Agent",
            confidence_score=0.82,
            discussion_state="Accepted",
            verification_status="High-confidence potential issue",
            root_cause="Multi-pass iteration on collections of unknown volume.",
            impact="Elevated memory residency and execution time when processing million-element batches.",
            actionability_score=0.85,
            is_publishable=True,
            is_resolved=False,
        )

        session.add_all([f1, f2, f3])
        await session.flush()

        # Add Agent Discussions
        d1 = AgentDiscussion(
            review_id=latest_review.id,
            finding_id=f1.id,
            agent_name="Bug Hunter",
            message_type="proposal",
            position="challenge",
            content="Detected unhandled division by zero: `len(values)` is 0 when values is an empty list `[]`.",
            evidence="demo_sample.py: line 9: `return sum(values) / len(values)`",
            source_reference="backend/app/demo_sample.py:8-10",
            round_number=1,
        )
        d2 = AgentDiscussion(
            review_id=latest_review.id,
            finding_id=f1.id,
            agent_name="Reviewer 2",
            message_type="critique",
            position="rebuttal",
            content="Does the type annotation `Optional[List[int]]` require handling `None` as well?",
            evidence="Type signature specifies Optional[List[int]], which permits None.",
            source_reference="backend/app/demo_sample.py:6",
            round_number=1,
        )
        d3 = AgentDiscussion(
            review_id=latest_review.id,
            finding_id=f1.id,
            agent_name="Verification Arbiter",
            message_type="verification",
            position="verdict",
            content="Empirically confirmed: calling calculate_average([]) raises ZeroDivisionError. Finding accepted as HIGH severity.",
            final_decision="Accepted",
            source_reference="backend/app/demo_sample.py:9",
            round_number=2,
            is_verified=True,
        )

        # Add discussions for finding 2 (Security)
        d4 = AgentDiscussion(
            review_id=latest_review.id,
            finding_id=f2.id,
            agent_name="Security Agent",
            message_type="proposal",
            position="challenge",
            content="CWE-89 SQL Injection detected: string formatting in SQL statement.",
            evidence="demo_sample.py: line 13: `f'SELECT * FROM {table_name}'`",
            source_reference="backend/app/demo_sample.py:13",
            round_number=1,
        )
        d5 = AgentDiscussion(
            review_id=latest_review.id,
            finding_id=f2.id,
            agent_name="Verification Arbiter",
            message_type="verification",
            position="verdict",
            content="Confirmed vulnerability: table names cannot be parameterized with bind variables. Whitelisting is mandatory.",
            final_decision="Accepted",
            source_reference="backend/app/demo_sample.py:12-14",
            round_number=2,
            is_verified=True,
        )

        session.add_all([d1, d2, d3, d4, d5])

        # Create AutoFix Patch for Finding 1
        unified_diff_str = (
            "--- a/backend/app/demo_sample.py\n"
            "+++ b/backend/app/demo_sample.py\n"
            "@@ -6,4 +6,6 @@\n"
            " def calculate_average(values: Optional[List[int]]) -> float:\n"
            '     """Calculate the arithmetic mean of a list of numbers."""\n'
            "-    return sum(values) / len(values)\n"
            "+    if not values:\n"
            "+        return 0.0\n"
            "+    return float(sum(values)) / len(values)\n"
        )
        rollback_diff_str = (
            "--- a/backend/app/demo_sample.py\n"
            "+++ b/backend/app/demo_sample.py\n"
            "@@ -6,6 +6,4 @@\n"
            " def calculate_average(values: Optional[List[int]]) -> float:\n"
            '     """Calculate the arithmetic mean of a list of numbers."""\n'
            "-    if not values:\n"
            "-        return 0.0\n"
            "-    return float(sum(values)) / len(values)\n"
            "+    return sum(values) / len(values)\n"
        )

        patch1 = Patch(
            finding_id=f1.id,
            original_code="    return sum(values) / len(values)",
            proposed_code="    if not values:\n        return 0.0\n    return float(sum(values)) / len(values)",
            diff_content=unified_diff_str,
            rollback_diff=rollback_diff_str,
            status="pending",
            sandbox_status="passed",
            formatter_status="passed",
            linter_status="passed",
            regression_status="passed",
        )
        session.add(patch1)
        await session.flush()

        # Add test run for patch
        test_run = TestRun(
            patch_id=patch1.id,
            test_framework="pytest",
            status="passed",
            total_tests=3,
            passed_tests=3,
            failed_tests=0,
            skipped_tests=0,
            execution_time_seconds=0.08,
            stdout_log="test_calculate_average_empty_list PASSED\ntest_calculate_average_none PASSED\ntest_calculate_average_valid PASSED\n3 passed in 0.08s",
        )
        session.add(test_run)

        # Update review metrics
        latest_review.quality_score = 78.5
        latest_review.security_score = 65.0
        latest_review.performance_score = 85.0
        latest_review.status = "completed"

        await session.commit()
        print(f"Successfully populated {latest_review.id}:")
        print(f"  - 3 Findings ({f1.id}, {f2.id}, {f3.id})")
        print(f"  - 5 Deliberation Discussions")
        print(f"  - 1 Validated AutoFix Patch ({patch1.id})")


if __name__ == "__main__":
    asyncio.run(populate())
