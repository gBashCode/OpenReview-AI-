"""Pull Request Impact, Modified Function, and Sensitive Change Detection Engine."""

import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.analyzer.diff_parser import ParsedDiffFile
from app.analyzer.schemas import (
    ChangeCategory,
    ChangedFileDTO,
    ChangedFunctionDTO,
    RiskFactorDTO,
    RiskLevel,
)
from app.indexing.ast_parser import ParsedSymbol, TreeSitterASTParser
from app.indexing.dependency_graph import DependencyGraph
from app.indexing.file_discovery import FileCategory, Language


class ImpactDetector:
    """Analyzes parsed diffs and repository context to discover modified functions,
    architectural impact, sensitive changes, and missing test coverage.
    """

    SENSITIVE_PATTERNS = {
        "Authentication": {
            "keywords": [
                "jwt",
                "token",
                "password",
                "login",
                "logout",
                "authenticate",
                "session",
                "bearer",
                "oauth",
                "secret_key",
                "credential",
                "hash_password",
                "verify_password",
            ],
            "paths": ["auth", "jwt", "login", "session"],
            "severity": RiskLevel.HIGH,
            "description": "Modifications in authentication logic, token generation, or credential handling.",
            "impact": 25.0,
        },
        "Authorization": {
            "keywords": [
                "permission",
                "role",
                "rbac",
                "is_superuser",
                "is_admin",
                "authorize",
                "has_permission",
                "access_control",
                "forbidden",
                "tenant_id",
            ],
            "paths": ["permissions", "policies", "rbac", "guard"],
            "severity": RiskLevel.HIGH,
            "description": "Changes in access control, role authorization, or tenant isolation policies.",
            "impact": 20.0,
        },
        "Payment & Billing": {
            "keywords": [
                "payment",
                "stripe",
                "checkout",
                "credit_card",
                "invoice",
                "billing",
                "subscription",
                "refund",
                "charge",
                "currency",
                "amount_cents",
            ],
            "paths": ["payment", "billing", "checkout", "stripe"],
            "severity": RiskLevel.CRITICAL,
            "description": "Modifications in financial transactions, payment gateways, or subscription logic.",
            "impact": 30.0,
        },
        "Database Migrations": {
            "keywords": [
                "alter table",
                "drop table",
                "drop column",
                "create table",
                "truncate",
                "op.add_column",
                "op.drop_column",
                "ondelete",
            ],
            "paths": ["alembic/versions", "migrations", "schema.sql", "flyway"],
            "severity": RiskLevel.HIGH,
            "description": "Database schema modifications or Alembic migration scripts.",
            "impact": 20.0,
        },
        "Public API Contract": {
            "keywords": [
                "@router.get",
                "@router.post",
                "@router.put",
                "@router.delete",
                "@router.patch",
                "@app.get",
                "@app.post",
                "export interface",
                "export type",
            ],
            "paths": ["api/v1", "endpoints", "routes", "controllers"],
            "severity": RiskLevel.MEDIUM,
            "description": "Changes to public HTTP REST endpoints or shared exported interfaces.",
            "impact": 15.0,
        },
        "Dependency Updates": {
            "keywords": [],
            "paths": [
                "package.json",
                "package-lock.json",
                "requirements.txt",
                "pyproject.toml",
                "go.mod",
                "go.sum",
                "pom.xml",
                "build.gradle",
                "pnpm-lock.yaml",
                "yarn.lock",
            ],
            "severity": RiskLevel.LOW,
            "description": "Third-party dependency manifest updates.",
            "impact": 10.0,
        },
    }

    def __init__(self):
        self.ast_parser = TreeSitterASTParser()

    def identify_modified_functions(
        self,
        parsed_files: List[ParsedDiffFile],
        repo_symbols: Optional[List[Any]] = None,
    ) -> List[ChangedFunctionDTO]:
        """Maps modified diff lines to AST functions, methods, and classes."""
        changed_functions: List[ChangedFunctionDTO] = []
        file_to_symbols: Dict[str, List[Any]] = {}

        if repo_symbols:
            for s in repo_symbols:
                file_to_symbols.setdefault(s.file_path, []).append(s)

        for pf in parsed_files:
            file_path = pf.new_path.replace("\\", "/")
            modified_lines = set(pf.modified_line_numbers)
            if not modified_lines:
                continue

            symbols = file_to_symbols.get(file_path, [])

            # If no cached symbols in DB, parse file on-the-fly if local content exists
            if not symbols:
                symbols = self._parse_on_the_fly(pf)

            for sym in symbols:
                s_name = getattr(sym, "name", "")
                s_kind = getattr(sym, "kind", "function")
                s_start = getattr(sym, "line_number", 1)
                s_end = getattr(sym, "end_line_number", None) or s_start
                s_sig = getattr(sym, "signature", None)

                sym_lines = set(range(s_start, s_end + 1))
                if sym_lines.intersection(modified_lines):
                    # Check if additions are in this function
                    has_additions = any(line in sym_lines for line, _ in pf.added_lines)
                    has_deletions = any(line in sym_lines for line, _ in pf.removed_lines)

                    change_type = "modified"
                    if has_additions and not has_deletions:
                        change_type = "added"
                    elif has_deletions and not has_additions:
                        change_type = "removed"

                    changed_functions.append(
                        ChangedFunctionDTO(
                            name=s_name,
                            kind=s_kind,
                            file_path=file_path,
                            line_number=s_start,
                            end_line_number=s_end,
                            signature=s_sig,
                            change_type=change_type,
                        )
                    )

        return changed_functions

    def detect_sensitive_changes(
        self,
        parsed_files: List[ParsedDiffFile],
    ) -> List[RiskFactorDTO]:
        """Detects security, auth, payment, and database migration risks from diff content."""
        detected_factors: List[RiskFactorDTO] = []

        for category_name, rule in self.SENSITIVE_PATTERNS.items():
            matching_files: Set[str] = set()

            for pf in parsed_files:
                file_path_lower = pf.new_path.lower()

                # Check path pattern
                path_match = any(p in file_path_lower for p in rule["paths"])

                # Check content keywords in added/removed lines
                keyword_match = False
                if rule["keywords"]:
                    for _, line_text in pf.added_lines:
                        text_lower = line_text.lower()
                        if any(kw in text_lower for kw in rule["keywords"]):
                            keyword_match = True
                            break

                if path_match or keyword_match:
                    matching_files.add(pf.new_path)

            if matching_files:
                detected_factors.append(
                    RiskFactorDTO(
                        name=f"{category_name} Change Detected",
                        severity=rule["severity"],
                        description=rule["description"],
                        score_impact=rule["impact"],
                        evidence_files=sorted(list(matching_files)),
                    )
                )

        return detected_factors

    def classify_change_types(
        self,
        parsed_files: List[ParsedDiffFile],
        pr_title: str = "",
        pr_description: str = "",
        sensitive_factors: Optional[List[RiskFactorDTO]] = None,
    ) -> List[str]:
        """Classifies the Pull Request into architectural change categories."""
        categories: Set[str] = set()
        title_lower = pr_title.lower()
        desc_lower = (pr_description or "").lower()
        all_text = f"{title_lower} {desc_lower}"

        total_additions = sum(f.additions for f in parsed_files)
        total_deletions = sum(f.deletions for f in parsed_files)

        # 1. Bug Fix
        if any(w in all_text for w in ["fix", "bug", "patch", "resolve", "hotfix", "issue"]):
            categories.add(ChangeCategory.BUG_FIX.value)

        # 2. Security-sensitive
        if sensitive_factors:
            sec_factors = [f for f in sensitive_factors if f.severity in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
            if sec_factors or any(w in all_text for w in ["security", "auth", "cve", "sanitize", "vulnerability"]):
                categories.add(ChangeCategory.SECURITY_SENSITIVE.value)

        # 3. Dependency update
        if any(f.status != "deleted" and any(m in f.new_path for m in ["package.json", "requirements.txt", "go.mod", "pom.xml"]) for f in parsed_files):
            categories.add(ChangeCategory.DEPENDENCY_UPDATE.value)

        # 4. Configuration change
        if any(f.new_path.endswith((".yml", ".yaml", ".toml", ".ini", ".env.example")) for f in parsed_files):
            categories.add(ChangeCategory.CONFIGURATION_CHANGE.value)

        # 5. Test modification
        has_tests = any(
            "test" in f.new_path.lower() or f.new_path.endswith(("_test.py", ".test.ts", "_test.go", "Test.java"))
            for f in parsed_files
        )
        if has_tests:
            categories.add(ChangeCategory.TEST_MODIFICATION.value)

        # 6. Performance-related
        if any(w in all_text for w in ["perf", "performance", "optimize", "cache", "slow", "latency", "benchmark"]):
            categories.add(ChangeCategory.PERFORMANCE_RELATED.value)
        for pf in parsed_files:
            for _, line in pf.added_lines:
                if any(w in line.lower() for w in ["cache", "lru_cache", "redis", "bulk_create", "index"]):
                    categories.add(ChangeCategory.PERFORMANCE_RELATED.value)
                    break

        # 7. Refactoring
        if any(w in all_text for w in ["refactor", "cleanup", "reorganize", "restructure"]):
            categories.add(ChangeCategory.REFACTORING.value)
        elif total_additions > 20 and total_deletions > 20 and abs(total_additions - total_deletions) < 50:
            categories.add(ChangeCategory.REFACTORING.value)

        # 8. New feature
        if any(w in all_text for w in ["feat", "feature", "add", "implement", "support", "new"]):
            categories.add(ChangeCategory.NEW_FEATURE.value)
        elif total_additions > total_deletions * 2 and total_additions > 30:
            categories.add(ChangeCategory.NEW_FEATURE.value)

        if not categories:
            categories.add(ChangeCategory.REFACTORING.value)

        return sorted(list(categories))

    def detect_affected_modules(self, parsed_files: List[ParsedDiffFile]) -> List[str]:
        """Identifies distinct package and module domains touched by the diff."""
        modules: Set[str] = set()
        for pf in parsed_files:
            parts = pf.new_path.replace("\\", "/").split("/")
            if len(parts) > 1:
                modules.add(parts[0] if len(parts) == 2 else f"{parts[0]}/{parts[1]}")
            else:
                modules.add("root")
        return sorted(list(modules))

    def detect_affected_tests(
        self,
        parsed_files: List[ParsedDiffFile],
        dep_graph: Optional[DependencyGraph] = None,
    ) -> Tuple[List[str], bool]:
        """Discovers existing related test files and flags missing test coverage."""
        affected_tests: Set[str] = set()
        source_files_changed = False
        test_files_changed = False

        for pf in parsed_files:
            path_lower = pf.new_path.lower()
            is_test = (
                "test" in path_lower
                or path_lower.endswith(("_test.py", ".test.ts", ".spec.ts", "_test.go", "test.java"))
            )
            if is_test:
                test_files_changed = True
                affected_tests.add(pf.new_path)
            elif not pf.new_path.endswith((".md", ".txt", ".json", ".yaml", ".yml", ".png", ".svg")):
                source_files_changed = True
                if dep_graph:
                    related = dep_graph.get_related_tests(pf.new_path)
                    affected_tests.update(related)

        missing_test_coverage = source_files_changed and not test_files_changed
        return sorted(list(affected_tests)), missing_test_coverage

    def _parse_on_the_fly(self, pf: ParsedDiffFile) -> List[Any]:
        """Parses added content on the fly when DB symbols are unavailable."""
        content = "\n".join(text for _, text in pf.added_lines)
        if not content.strip():
            return []

        ext = os.path.splitext(pf.new_path)[1].lower()
        lang_map = {
            ".py": Language.PYTHON,
            ".ts": Language.TYPESCRIPT,
            ".tsx": Language.TYPESCRIPT,
            ".js": Language.JAVASCRIPT,
            ".java": Language.JAVA,
            ".go": Language.GO,
        }
        lang = lang_map.get(ext)
        if not lang:
            return []

        symbols, _ = self.ast_parser.parse_file(pf.new_path, content, lang)
        return symbols
