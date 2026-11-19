"""Centralized Prompt Management and Template System."""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Optional, Tuple
from app.core.ai.base import LLMMessage, MessageRole
from app.core.exceptions import AppException


@dataclass
class PromptTemplate:
    """Represents a versioned prompt template with variable interpolation."""

    name: str
    system_prompt: str
    user_prompt: str
    description: str = ""
    version: str = "1.0.0"
    required_variables: List[str] = field(default_factory=list)

    def render(self, **kwargs) -> Tuple[str, str]:
        """Renders system and user prompts with provided variables."""
        missing = [v for v in self.required_variables if v not in kwargs]
        if missing:
            raise AppException(
                f"Missing required variables for prompt template '{self.name}': {', '.join(missing)}",
                status_code=400,
            )

        rendered_system = self._interpolate(self.system_prompt, kwargs)
        rendered_user = self._interpolate(self.user_prompt, kwargs)
        return rendered_system, rendered_user

    def _interpolate(self, text: str, variables: Dict[str, Any]) -> str:
        for k, v in variables.items():
            text = text.replace(f"{{{k}}}", str(v))
        return text


class PromptManager:
    """Central registry and renderer for all AI prompts and role instructions."""

    def __init__(self):
        self._templates: Dict[str, PromptTemplate] = {}
        self._register_default_templates()

    def register_template(self, template: PromptTemplate):
        self._templates[template.name] = template

    def get_template(self, name: str) -> PromptTemplate:
        tmpl = self._templates.get(name)
        if not tmpl:
            raise AppException(f"Prompt template '{name}' not found in registry.", status_code=404)
        return tmpl

    def format_messages(self, template_name: str, **kwargs) -> List[LLMMessage]:
        """Renders template into standardized LLMMessage objects ready for providers."""
        template = self.get_template(template_name)
        system_text, user_text = template.render(**kwargs)
        messages = []
        if system_text.strip():
            messages.append(LLMMessage(role=MessageRole.SYSTEM, content=system_text))
        if user_text.strip():
            messages.append(LLMMessage(role=MessageRole.USER, content=user_text))
        return messages

    def _register_default_templates(self):
        """Registers system-wide prompts for autonomous review agents."""

        # 1. Security Sentinel
        self.register_template(
            PromptTemplate(
                name="security_sentinel",
                description="Detects OWASP vulnerabilities, token flaws, and injection vectors.",
                required_variables=["pr_title", "changed_files_summary", "diff_content"],
                system_prompt="""You are the Security Sentinel AI agent for OpenReview AI.
Your sole mission is discovering security vulnerabilities, unauthorized access risks, injection vectors,
unsafe credential handling, cryptography weaknesses, and sensitive data leakage.
Always verify evidence with real file paths and line numbers. Never fabricate context.""",
                user_prompt="""Review the following Pull Request changes:

PR Title: {pr_title}
Changed Files:
{changed_files_summary}

Unified Diff:
```diff
{diff_content}
```

Identify any security vulnerabilities, their exact line numbers, and provide clear remediation guidance.""",
            )
        )

        # 2. Bug Hunter
        self.register_template(
            PromptTemplate(
                name="bug_hunter",
                description="Finds logic errors, null pointers, race conditions, and regressions.",
                required_variables=["pr_title", "diff_content"],
                system_prompt="""You are the Bug Hunter AI agent for OpenReview AI.
Your specialty is finding logic traps, unhandled edge cases, off-by-one errors, race conditions,
unhandled exceptions, and potential regressions.
Analyze every changed branch and condition thoroughly.""",
                user_prompt="""Review the logic changes in this Pull Request:

PR Title: {pr_title}

Unified Diff:
```diff
{diff_content}
```

List any logical flaws, unexpected side effects, or unhandled exceptions with line numbers.""",
            )
        )

        # 3. Performance Optimizer
        self.register_template(
            PromptTemplate(
                name="performance_optimizer",
                description="Detects database query inefficiencies, memory leaks, and blocking operations.",
                required_variables=["pr_title", "diff_content"],
                system_prompt="""You are the Performance Optimizer AI agent for OpenReview AI.
Your focus is algorithmic efficiency, database query optimization (N+1 queries, missing indexes),
memory consumption, CPU utilization, and asynchronous non-blocking execution.""",
                user_prompt="""Analyze performance implications of this Pull Request:

PR Title: {pr_title}

Unified Diff:
```diff
{diff_content}
```

Identify any bottlenecks, unindexed database queries, or excessive resource usage.""",
            )
        )

        # 4. Architecture Reviewer
        self.register_template(
            PromptTemplate(
                name="architecture_reviewer",
                description="Reviews system design, clean architecture, and API backward compatibility.",
                required_variables=["pr_title", "diff_content"],
                system_prompt="""You are the Architecture Reviewer AI agent for OpenReview AI.
Your responsibility is enforcing clean architecture boundaries, domain isolation,
tenant data security, and ensuring public REST API backwards-compatibility.""",
                user_prompt="""Evaluate architectural integrity of this Pull Request:

PR Title: {pr_title}

Unified Diff:
```diff
{diff_content}
```

Assess API stability, layer boundaries, and design patterns.""",
            )
        )

        # 5. AutoFix Patch Generator
        self.register_template(
            PromptTemplate(
                name="autofix_generator",
                description="Generates syntactically correct git diff patches to fix review findings.",
                required_variables=["finding_description", "file_path", "original_code"],
                system_prompt="""You are the AutoFix Generator for OpenReview AI.
Generate a clean, minimal, syntactically correct drop-in replacement patch that resolves
the specified code review issue without altering unrelated logic.""",
                user_prompt="""Resolve the following review finding:

Issue: {finding_description}
Target File: {file_path}

Original Code:
```
{original_code}
```

Provide the fixed replacement code and explanation.""",
            )
        )


# Global singleton instance
prompt_manager = PromptManager()
