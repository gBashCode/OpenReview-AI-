"""AutoFix Patch Utilities: Diff Generation, Validation, Application, Rollback, Formatter & Linter."""

import ast
import difflib
import re
from typing import List, Optional, Tuple


class PatchApplier:
    """Provides unified diff parsing, validation, dry-run application, and rollback generation."""

    @staticmethod
    def compute_unified_diff(
        original_code: str,
        proposed_code: str,
        file_path: str = "file.py",
    ) -> str:
        """Computes a standard unified diff between original and proposed code."""
        orig_lines = original_code.splitlines(keepends=True)
        prop_lines = proposed_code.splitlines(keepends=True)

        # Ensure trailing newlines
        if orig_lines and not orig_lines[-1].endswith("\n"):
            orig_lines[-1] += "\n"
        if prop_lines and not prop_lines[-1].endswith("\n"):
            prop_lines[-1] += "\n"

        diff_gen = difflib.unified_diff(
            orig_lines,
            prop_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
        )
        return "".join(diff_gen)

    @staticmethod
    def validate_unified_diff(diff_content: str) -> Tuple[bool, Optional[str]]:
        """Validates that a diff string adheres to the standard unified diff format."""
        if not diff_content or not diff_content.strip():
            return False, "Diff content is empty."

        lines = diff_content.strip().splitlines()

        has_header_a = any(l.startswith("--- ") for l in lines)
        has_header_b = any(l.startswith("+++ ") for l in lines)
        has_hunk = any(l.startswith("@@ ") for l in lines)

        if not (has_header_a and has_header_b and has_hunk):
            return (
                False,
                "Malformed diff: Missing required unified diff headers ('--- a/', '+++ b/', or '@@ -l,s +l,s @@').",
            )

        for line in lines:
            if line.startswith(("--- ", "+++ ", "@@ ", "+", "-", " ", "\\")):
                continue
            return (
                False,
                f"Invalid unified diff line prefix '{line[:10]}...'. Must begin with '+', '-', or space.",
            )

        return True, None

    @classmethod
    def apply_diff(
        cls,
        original_code: str,
        diff_content: str,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Applies a unified diff to original source code in memory (dry run / patch verification)."""
        is_valid, err = cls.validate_unified_diff(diff_content)
        if not is_valid:
            return False, None, f"Diff validation failed: {err}"

        orig_lines = original_code.splitlines(keepends=True)
        diff_lines = diff_content.splitlines(keepends=True)

        patched_lines: List[str] = []
        orig_idx = 0

        # Extract hunks
        hunk_regex = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@")

        i = 0
        while i < len(diff_lines):
            line = diff_lines[i]
            if not line.startswith("@@"):
                i += 1
                continue

            match = hunk_regex.match(line)
            if not match:
                return False, None, f"Invalid hunk header: {line.strip()}"

            start_orig = int(match.group(1)) - 1
            i += 1

            # Advance original code up to hunk start
            while orig_idx < start_orig and orig_idx < len(orig_lines):
                patched_lines.append(orig_lines[orig_idx])
                orig_idx += 1

            # Process hunk changes
            while i < len(diff_lines) and not diff_lines[i].startswith("@@"):
                hline = diff_lines[i]
                if hline.startswith(" "):
                    # Context line
                    if orig_idx < len(orig_lines):
                        orig_idx += 1
                    patched_lines.append(hline[1:])
                elif hline.startswith("-"):
                    # Removed line
                    if orig_idx < len(orig_lines):
                        orig_idx += 1
                elif hline.startswith("+"):
                    # Added line
                    patched_lines.append(hline[1:])
                elif hline.startswith("\\"):
                    # "\ No newline at end of file"
                    pass
                i += 1

        # Copy trailing lines from original
        while orig_idx < len(orig_lines):
            patched_lines.append(orig_lines[orig_idx])
            orig_idx += 1

        return True, "".join(patched_lines), None

    @classmethod
    def generate_rollback_diff(
        cls,
        original_code: str,
        proposed_code: str,
        file_path: str = "file.py",
    ) -> str:
        """Generates the inverse rollback patch to undo a proposed change."""
        return cls.compute_unified_diff(
            original_code=proposed_code,
            proposed_code=original_code,
            file_path=file_path,
        )

    @staticmethod
    def run_formatter(code: str, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """Formats code cleanly; for Python, uses AST parse/unparse or indentation formatting."""
        if file_path.endswith(".py"):
            try:
                tree = ast.parse(code)
                # ast.unparse formats standard clean Python
                formatted = ast.unparse(tree) + "\n"
                return True, formatted, None
            except Exception as e:
                return False, code, f"Formatter error: {str(e)}"

        # General clean trim for other languages
        return True, code.rstrip() + "\n", None

    @staticmethod
    def run_linter(code: str, file_path: str) -> Tuple[bool, List[str]]:
        """Runs syntax and basic lint validation to guarantee no syntax errors were introduced."""
        errors: List[str] = []

        if file_path.endswith(".py"):
            try:
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"Syntax error on line {e.lineno}: {e.msg}")

        # Basic balanced braces check
        open_braces = code.count("{") - code.count("}")
        if open_braces != 0:
            errors.append(f"Unbalanced curly braces: difference of {open_braces}")

        open_parens = code.count("(") - code.count(")")
        if open_parens != 0:
            errors.append(f"Unbalanced parentheses: difference of {open_parens}")

        return (len(errors) == 0), errors
