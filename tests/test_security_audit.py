"""Security Audit and Defense Verification Tests.

Validates critical security controls across:
- Sandbox boundary and directory traversal prevention
- Secret sanitization and environment scrubbing
- Webhook HMAC-SHA256 signature enforcement
- Prompt injection defense directives in agent system prompts
- Production environment configuration safeguards
"""

import os
import tempfile
import pytest
from pydantic import ValidationError
from app.core.config import Settings, get_settings
from app.github.github_webhook_service import GitHubWebhookService
from app.orchestration.prompts import (
    BUG_HUNTER_SYSTEM_PROMPT,
    CONTEXT_AGENT_SYSTEM_PROMPT,
    PROMPT_INJECTION_DEFENSE_DIRECTIVE,
    REVIEWER2_SYSTEM_PROMPT,
    SECURITY_AGENT_SYSTEM_PROMPT,
    VERIFICATION_AGENT_SYSTEM_PROMPT,
)
from app.sandbox.security import SandboxSecurityEnforcer


def test_sandbox_path_traversal_prevention():
    """Verify that path traversal attempts in the sandbox runner are detected and rejected."""
    enforcer = SandboxSecurityEnforcer()
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Valid subpaths within sandbox boundary
        safe_path = enforcer.validate_safe_path(temp_dir, "app/services/checkout.py")
        assert safe_path.startswith(temp_dir)

        # 2. Path traversal via ../ attempting to escape sandbox directory
        with pytest.raises(ValueError, match="Security violation: path traversal detected"):
            enforcer.validate_safe_path(temp_dir, "../../../etc/passwd")

        # 3. Path traversal attempting to escape via nested relative traversal
        with pytest.raises(ValueError, match="Security violation: path traversal detected"):
            enforcer.validate_safe_path(temp_dir, "nested/dir/../../../../sensitive.key")


def test_sandbox_secret_scrubbing_and_isolation():
    """Verify that host environment variables and secrets are completely scrubbed from execution."""
    enforcer = SandboxSecurityEnforcer()
    custom_env = {
        "GITHUB_TOKEN": "ghp_super_secret_token_12345",
        "DATABASE_URL": "postgresql://user:pass@host:5432/db",
        "AWS_SECRET_ACCESS_KEY": "AKIAIOSFODNN7EXAMPLE",
        "SAFE_BUILD_FLAG": "enabled",
    }
    clean_env = enforcer.sanitize_environment(custom_env=custom_env)

    # Secrets must NOT be present
    assert "GITHUB_TOKEN" not in clean_env
    assert "DATABASE_URL" not in clean_env
    assert "AWS_SECRET_ACCESS_KEY" not in clean_env

    # Safe variables are preserved
    assert clean_env.get("SAFE_BUILD_FLAG") == "enabled"
    assert clean_env.get("OPENREVIEW_SANDBOX") == "true"
    assert clean_env.get("SANDBOX_NETWORK_ISOLATED") == "true"


def test_webhook_signature_rejection_when_secret_unset(monkeypatch):
    """Verify that webhooks are rejected when the webhook secret is missing (fails closed)."""
    settings = get_settings()
    monkeypatch.setattr(settings, "GITHUB_WEBHOOK_SECRET", None)

    payload_body = b'{"action": "synchronize"}'
    # Must reject when secret is None
    assert GitHubWebhookService.verify_signature(payload_body, "sha256=abcdef123456") is False
    assert GitHubWebhookService.verify_signature(payload_body, None) is False


def test_prompt_injection_directives_embedded_in_system_prompts():
    """Verify that immutable prompt injection defense directives are present in all core agents."""
    assert "CRITICAL SECURITY DIRECTIVE (IMMUTABLE)" in PROMPT_INJECTION_DEFENSE_DIRECTIVE
    assert "Ignore previous instructions" in PROMPT_INJECTION_DEFENSE_DIRECTIVE

    # Verify every critical agent system prompt embeds the directive
    prompts_to_check = [
        CONTEXT_AGENT_SYSTEM_PROMPT,
        BUG_HUNTER_SYSTEM_PROMPT,
        SECURITY_AGENT_SYSTEM_PROMPT,
        REVIEWER2_SYSTEM_PROMPT,
        VERIFICATION_AGENT_SYSTEM_PROMPT,
    ]
    for prompt in prompts_to_check:
        assert "CRITICAL SECURITY DIRECTIVE (IMMUTABLE)" in prompt
        assert "<untrusted_code_diff>" in prompt


def test_production_secret_key_minimum_length_and_default_prevention():
    """Verify that production environments enforce strict secret keys and fail on default values."""
    # Default secret key must fail
    with pytest.raises(ValidationError, match="SECRET_KEY must be changed from default in production"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="openreview-development-secret-key-change-in-production",
            GITHUB_WEBHOOK_SECRET="whsec_12345678901234567890123456789012",
        )

    # Short secret key (< 32 chars) must fail
    with pytest.raises(ValidationError, match="SECRET_KEY must be at least 32 characters long"):
        Settings(
            APP_ENV="production",
            SECRET_KEY="short-secret-key",
            GITHUB_WEBHOOK_SECRET="whsec_12345678901234567890123456789012",
        )

    # Valid secret key (>= 32 chars) and webhook secret succeeds
    prod = Settings(
        APP_ENV="production",
        SECRET_KEY="very-long-and-secure-random-secret-key-for-jwt-signing-2026",
        GITHUB_WEBHOOK_SECRET="whsec_12345678901234567890123456789012",
    )
    assert prod.is_production
