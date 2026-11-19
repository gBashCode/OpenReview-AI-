"""Verification TestRun Pydantic schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TestRunBase(BaseModel):
    patch_id: str
    status: str = "pending"  # pending, running, passed, failed, error
    test_framework: str = "pytest"
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    execution_time_seconds: Optional[float] = None


class TestRunCreate(BaseModel):
    patch_id: str
    test_framework: Optional[str] = "pytest"


class TestRunRead(TestRunBase):
    id: str
    stdout_log: Optional[str] = None
    stderr_log: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
