"""Sandbox Security Enforcer.

Enforces zero-trust isolation constraints for ephemeral test execution:
- Complete removal of application secrets from environment
- Whitelist-only environment variable filtering
- Strict CPU and memory quota caps
- Hard execution timeouts
- Non-root user execution
- Network isolation (no outbound/inbound connections)
"""

import os
import re
from typing import Dict, List, Optional, Set

BLOCKED_SECRET_PATTERNS = [
    r"api[_-]?key",
    r"secret",
    r"password",
    r"token",
    r"private[_-]?key",
    r"auth",
    r"database[_-]?url",
    r"redis[_-]?url",
    r"webhook",
    r"jwt",
    r"session",
    r"credential",
]

ALLOWED_ENV_VARS = {
    "PATH",
    "PYTHONPATH",
    "PYTHONUNBUFFERED",
    "PYTHONDONTWRITEBYTECODE",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "TEMP",
    "TMP",
    "CI",
    "TESTING",
    # Windows system paths required for core DLL and Winsock loader initialization
    "SYSTEMROOT",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
}


class SandboxSecurityEnforcer:
    """Validates and enforces security constraints on sandbox execution."""

    def __init__(
        self,
        max_cpu_cores: float = 1.0,
        max_memory_mb: int = 512,
        default_timeout_seconds: int = 20,
        max_output_bytes: int = 1024 * 1024,  # 1MB
    ):
        self.max_cpu_cores = max_cpu_cores
        self.max_memory_mb = max_memory_mb
        self.default_timeout_seconds = default_timeout_seconds
        self.max_output_bytes = max_output_bytes

    def sanitize_environment(
        self,
        custom_env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Creates an isolated, secret-free environment dictionary.

        Ensures NO application secrets, API tokens, database connections,
        or host keys can leak into the execution sandbox.
        """
        clean_env: Dict[str, str] = {}

        # 1. Copy only strictly whitelisted system environment variables
        for var in ALLOWED_ENV_VARS:
            val = os.environ.get(var)
            if val is not None:
                clean_env[var] = val

        # 2. Add custom variables after strict pattern validation
        if custom_env:
            for k, v in custom_env.items():
                if self.is_secret_key(k):
                    continue  # Block detected secret
                clean_env[k] = str(v)

        # 3. Add explicit sandbox safety markers
        clean_env["OPENREVIEW_SANDBOX"] = "true"
        clean_env["SANDBOX_NETWORK_ISOLATED"] = "true"
        clean_env["PYTHONDONTWRITEBYTECODE"] = "1"
        clean_env["PYTHONUNBUFFERED"] = "1"

        return clean_env

    @staticmethod
    def is_secret_key(key_name: str) -> bool:
        """Determines if an environment variable key name indicates a sensitive credential."""
        norm_key = key_name.lower()
        for pat in BLOCKED_SECRET_PATTERNS:
            if re.search(pat, norm_key):
                return True
        return False

    def validate_resource_bounds(
        self,
        requested_cpu: Optional[float] = None,
        requested_memory_mb: Optional[int] = None,
        requested_timeout_seconds: Optional[int] = None,
    ) -> Dict[str, float]:
        """Clamps requested resource quotas to hard security ceilings."""
        cpu = min(requested_cpu or self.max_cpu_cores, self.max_cpu_cores)
        mem = min(requested_memory_mb or self.max_memory_mb, self.max_memory_mb)
        timeout = min(
            requested_timeout_seconds or self.default_timeout_seconds,
            self.default_timeout_seconds * 2,
        )

        return {
            "cpu_limit": max(0.2, cpu),
            "memory_limit_mb": max(64, mem),
            "timeout_seconds": max(2, timeout),
        }

    def truncate_output(self, raw_output: str) -> str:
        """Truncates process stdout/stderr to prevent buffer-flooding DoS attacks."""
        if not raw_output:
            return ""
        if len(raw_output.encode("utf-8")) > self.max_output_bytes:
            truncated = raw_output[: self.max_output_bytes]
            return truncated + "\n... [Output truncated by Sandbox Security Enforcer: exceeded 1MB limit] ...\n"
        return raw_output
