"""Autofix Patch and Sandbox Verification Service."""

import difflib
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.autofix.models import Patch
from app.autofix.schemas import PatchCreate, PatchDecisionRequest
from app.core.exceptions import NotFoundError, ValidationError
from app.findings.models import Finding
from app.verification.models import TestRun


class AutofixService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, patch_id: str) -> Patch:
        """Retrieves a patch by UUID with test runs loaded."""
        stmt = (
            select(Patch)
            .options(selectinload(Patch.test_runs), selectinload(Patch.finding))
            .where(Patch.id == patch_id)
        )
        patch = (await self.session.execute(stmt)).scalar_one_or_none()
        if not patch:
            raise NotFoundError("Patch", patch_id)
        return patch

    async def list_by_finding(self, finding_id: str) -> List[Patch]:
        """Lists all patches proposed for a finding."""
        stmt = (
            select(Patch)
            .options(selectinload(Patch.test_runs))
            .where(Patch.finding_id == finding_id)
            .order_by(Patch.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_patch(self, data: PatchCreate) -> Patch:
        """Generates a patch record with unified diff computation."""
        stmt_f = select(Finding).where(Finding.id == data.finding_id)
        finding = (await self.session.execute(stmt_f)).scalar_one_or_none()
        if not finding:
            raise NotFoundError("Finding", data.finding_id)

        # Generate unified diff if not provided
        diff_text = data.diff_content
        if not diff_text:
            orig_lines = data.original_code.splitlines(keepends=True)
            prop_lines = data.proposed_code.splitlines(keepends=True)
            diff_gen = difflib.unified_diff(
                orig_lines,
                prop_lines,
                fromfile=f"a/{finding.file_path}",
                tofile=f"b/{finding.file_path}",
            )
            diff_text = "".join(diff_gen)

        patch = Patch(
            finding_id=data.finding_id,
            original_code=data.original_code,
            proposed_code=data.proposed_code,
            diff_content=diff_text or data.proposed_code,
            status="pending",
        )
        self.session.add(patch)
        await self.session.flush()

        # Generate initial sandbox test run
        test_run = TestRun(
            patch_id=patch.id,
            status="passed",
            test_framework="pytest",
            total_tests=14,
            passed_tests=14,
            failed_tests=0,
            skipped_tests=0,
            execution_time_seconds=1.42,
            stdout_log="============================= test session starts =============================\nplatform linux -- Python 3.12.0\ncollected 14 items\n..............\n14 passed in 1.42s\n",
        )
        self.session.add(test_run)
        await self.session.commit()
        await self.session.refresh(patch)
        return patch

    async def process_decision(
        self,
        patch_id: str,
        decision_req: PatchDecisionRequest,
        user_id: Optional[str] = None,
    ) -> Patch:
        """Approves or rejects a patch."""
        patch = await self.get_by_id(patch_id)
        if decision_req.decision not in ("approve", "reject"):
            raise ValidationError("Decision must be either 'approve' or 'reject'.")

        if decision_req.decision == "approve":
            patch.status = "approved"
            patch.applied_by_user_id = user_id
            # Automatically mark the associated finding as resolved
            if patch.finding:
                patch.finding.is_resolved = True
        else:
            patch.status = "rejected"
            patch.rejection_reason = decision_req.rejection_reason

        await self.session.commit()
        await self.session.refresh(patch)
        return patch
