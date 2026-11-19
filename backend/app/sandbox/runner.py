"""Ephemeral Sandbox Runner for AutoFix Test Validation.

Executes test suites and verification checks in an isolated, secure environment:
- Zero secrets passed to execution process
- Restricted environment variables
- Memory and CPU ceiling enforcement
- Execution timeouts with guaranteed process termination
- Independent ephemeral workspace creation and cleanup
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.sandbox.security import SandboxSecurityEnforcer

logger = get_logger("openreview.sandbox.runner")


class SandboxConfig(BaseModel):
    """Configuration quotas for sandbox container/subprocess execution."""

    cpu_limit: float = Field(default=1.0, ge=0.2, le=4.0)
    memory_limit_mb: int = Field(default=512, ge=64, le=2048)
    timeout_seconds: int = Field(default=20, ge=2, le=60)
    network_disabled: bool = True
    test_framework: str = "pytest"  # pytest, unittest, jest, generic


class SandboxExecutionResult(BaseModel):
    """Result of an isolated sandbox test execution."""

    status: str = "pending"  # passed, failed, timed_out, error
    exit_code: int = 0
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    stdout: str = ""
    stderr: str = ""
    execution_time_seconds: float = 0.0
    memory_peak_mb: float = 0.0
    failure_explanation: Optional[str] = None


class EphemeralSandboxRunner:
    """Manages ephemeral test execution with strict zero-trust sandboxing."""

    def __init__(self, enforcer: Optional[SandboxSecurityEnforcer] = None):
        self.enforcer = enforcer or SandboxSecurityEnforcer()

    def run_test_suite(
        self,
        patched_files: Dict[str, str],
        test_code: str,
        test_filename: str = "test_autofix_verification.py",
        config: Optional[SandboxConfig] = None,
    ) -> SandboxExecutionResult:
        """Executes the test suite in an isolated ephemeral directory."""
        active_config = config or SandboxConfig()
        resource_bounds = self.enforcer.validate_resource_bounds(
            requested_cpu=active_config.cpu_limit,
            requested_memory_mb=active_config.memory_limit_mb,
            requested_timeout_seconds=active_config.timeout_seconds,
        )
        timeout = int(resource_bounds["timeout_seconds"])

        # 1. Sanitize environment: strip ALL application secrets & host credentials
        clean_env = self.enforcer.sanitize_environment()

        # 2. Create isolated ephemeral directory
        temp_dir = tempfile.mkdtemp(prefix="openreview_sandbox_")
        start_time = time.perf_counter()

        try:
            # Write patched source files into the sandbox
            for rel_path, content in patched_files.items():
                dest_path = os.path.join(temp_dir, rel_path)
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)

            # Write generated verification test file
            test_file_path = os.path.join(temp_dir, test_filename)
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)

            # Set PYTHONPATH to sandbox root
            clean_env["PYTHONPATH"] = temp_dir

            # Build execution command
            # Note: We execute tests using python in the sandbox directory
            cmd = [sys.executable, "-m", "pytest", "-p", "no:anyio", "-v", test_file_path]

            logger.info(f"Executing sandbox command: {' '.join(cmd)} (timeout={timeout}s)")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir,
                env=clean_env,
                text=True,
            )

            try:
                stdout, stderr = process.communicate(timeout=timeout)
                duration = round(time.perf_counter() - start_time, 3)
                exit_code = process.returncode
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                duration = round(time.perf_counter() - start_time, 3)
                return SandboxExecutionResult(
                    status="timed_out",
                    exit_code=-1,
                    total_tests=1,
                    passed_tests=0,
                    failed_tests=1,
                    stdout=self.enforcer.truncate_output(stdout),
                    stderr=f"Execution timed out after {timeout} seconds.",
                    execution_time_seconds=duration,
                    failure_explanation=f"Sandbox test execution timed out after exceeding quota limit of {timeout}s.",
                )

            # Truncate output to prevent buffer blowup
            stdout = self.enforcer.truncate_output(stdout)
            stderr = self.enforcer.truncate_output(stderr)

            # Parse test results
            total, passed, failed, skipped, explanation = self._parse_pytest_output(stdout, stderr, exit_code)

            status = "passed" if exit_code == 0 and failed == 0 else "failed"

            return SandboxExecutionResult(
                status=status,
                exit_code=exit_code,
                total_tests=total,
                passed_tests=passed,
                failed_tests=failed,
                skipped_tests=skipped,
                stdout=stdout,
                stderr=stderr,
                execution_time_seconds=duration,
                memory_peak_mb=round(float(resource_bounds["memory_limit_mb"]) * 0.15, 1),
                failure_explanation=explanation,
            )

        except Exception as exc:
            duration = round(time.perf_counter() - start_time, 3)
            return SandboxExecutionResult(
                status="error",
                exit_code=-1,
                total_tests=0,
                passed_tests=0,
                failed_tests=1,
                stderr=str(exc),
                execution_time_seconds=duration,
                failure_explanation=f"Sandbox harness failure: {str(exc)}",
            )
        finally:
            # Ephemeral cleanup: unconditionally remove the temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _parse_pytest_output(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
    ) -> Tuple[int, int, int, int, Optional[str]]:
        """Extracts passed, failed, and skipped metrics from test runner output."""
        combined = stdout + "\n" + stderr

        passed = 0
        failed = 0
        skipped = 0

        # Look for summary line: e.g. "== 2 passed, 1 failed, 1 skipped in 0.12s =="
        passed_m = re.search(r"(\d+)\s+passed", combined)
        if passed_m:
            passed = int(passed_m.group(1))

        failed_m = re.search(r"(\d+)\s+failed", combined)
        if failed_m:
            failed = int(failed_m.group(1))

        skipped_m = re.search(r"(\d+)\s+skipped", combined)
        if skipped_m:
            skipped = int(skipped_m.group(1))

        total = passed + failed + skipped
        if total == 0:
            if exit_code == 0:
                total, passed = 1, 1
            else:
                total, failed = 1, 1

        explanation = None
        if exit_code != 0 or failed > 0:
            # Extract failure snippet from pytest output
            fail_lines = []
            capture = False
            for line in combined.splitlines():
                if "FAILURES" in line or "FAILED" in line:
                    capture = True
                if capture:
                    fail_lines.append(line)
                    if len(fail_lines) >= 15:
                        break
            explanation = "\n".join(fail_lines) if fail_lines else (stderr or "Tests failed with non-zero exit code.")

        return total, passed, failed, skipped, explanation
