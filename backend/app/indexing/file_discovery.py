"""Repository File Discovery, Language Detection, Classification, and SHA-256 Hashing."""

from dataclasses import dataclass
from enum import Enum
import fnmatch
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


class Language(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    GO = "go"
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    MARKDOWN = "markdown"
    SQL = "sql"
    SHELL = "shell"
    UNKNOWN = "unknown"


class FileCategory(str, Enum):
    SOURCE_CODE = "source_code"
    TEST = "test"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    DATABASE_MIGRATION = "database_migration"
    ASSET_BINARY = "asset_binary"
    IGNORED = "ignored"


# File extension to Language mapping
EXTENSION_LANGUAGE_MAP: Dict[str, Language] = {
    ".py": Language.PYTHON,
    ".pyw": Language.PYTHON,
    ".js": Language.JAVASCRIPT,
    ".jsx": Language.JAVASCRIPT,
    ".mjs": Language.JAVASCRIPT,
    ".cjs": Language.JAVASCRIPT,
    ".ts": Language.TYPESCRIPT,
    ".tsx": Language.TYPESCRIPT,
    ".mts": Language.TYPESCRIPT,
    ".cts": Language.TYPESCRIPT,
    ".java": Language.JAVA,
    ".go": Language.GO,
    ".json": Language.JSON,
    ".yaml": Language.YAML,
    ".yml": Language.YAML,
    ".toml": Language.TOML,
    ".md": Language.MARKDOWN,
    ".markdown": Language.MARKDOWN,
    ".sql": Language.SQL,
    ".sh": Language.SHELL,
    ".bash": Language.SHELL,
    ".zsh": Language.SHELL,
}

# Well-known configuration filenames
CONFIG_FILENAMES: Set[str] = {
    "package.json",
    "tsconfig.json",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "pipfile",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "go.mod",
    "go.sum",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "alembic.ini",
    ".env.example",
    "vite.config.ts",
    "vite.config.js",
    "webpack.config.js",
    "jest.config.js",
    "jest.config.ts",
    "eslint.config.js",
    "tailwind.config.js",
    "tailwind.config.ts",
    "Makefile",
}

# Directories always excluded from indexing
DEFAULT_EXCLUDED_DIRS: Set[str] = {
    ".git",
    ".github",
    ".svn",
    ".hg",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".next",
    "target",
    "vendor",
    ".idea",
    ".vscode",
    "coverage",
    ".cache",
    "out",
    "bin",
    "obj",
    ".turbo",
    ".husky",
}

# File extensions always excluded
DEFAULT_EXCLUDED_EXTS: Set[str] = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".class",
    ".jar",
    ".war",
    ".o",
    ".a",
    ".map",
    ".min.js",
    ".min.css",
    ".lock",
    ".DS_Store",
    "Thumbs.db",
}


@dataclass
class DiscoveredFile:
    """Represents a discovered repository file with metadata."""

    relative_path: str
    full_path: str
    size_bytes: int
    sha256_hash: str
    language: Language
    category: FileCategory
    is_binary: bool
    lines_count: int = 0


class GitIgnoreMatcher:
    """Evaluates .gitignore patterns against repository-relative file paths."""

    def __init__(self, root_dir: Path, custom_rules: Optional[List[str]] = None):
        self.rules: List[Tuple[bool, str]] = []  # (is_negation, pattern)
        self._load_gitignore(root_dir)
        if custom_rules:
            for rule in custom_rules:
                self._add_rule(rule)

    def _load_gitignore(self, root_dir: Path):
        gitignore_path = root_dir / ".gitignore"
        if gitignore_path.is_file():
            try:
                with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        self._add_rule(line)
            except Exception:
                pass

    def _add_rule(self, line: str):
        line = line.strip()
        if not line or line.startswith("#"):
            return
        is_negation = line.startswith("!")
        if is_negation:
            line = line[1:].strip()
        pattern = line.rstrip("/")
        self.rules.append((is_negation, pattern))

    def is_ignored(self, rel_path: str) -> bool:
        normalized = rel_path.replace("\\", "/")
        path_parts = normalized.split("/")

        ignored = False
        for is_negation, pattern in self.rules:
            # Match directly or match directory prefix
            if "/" in pattern:
                match = fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(normalized, f"{pattern}/*")
            else:
                match = any(fnmatch.fnmatch(part, pattern) for part in path_parts)

            if match:
                ignored = not is_negation
        return ignored


class FileDiscoveryService:
    """Discovers, filters, classifies, and hashes repository files."""

    def __init__(
        self,
        max_file_size_bytes: int = 500 * 1024,  # 500 KB limit for AST parsing
        custom_ignore_rules: Optional[List[str]] = None,
    ):
        self.max_file_size_bytes = max_file_size_bytes
        self.custom_ignore_rules = custom_ignore_rules or []

    def discover_repository(self, root_path: str) -> List[DiscoveredFile]:
        """Scans root_path recursively and returns a filtered list of DiscoveredFile objects."""
        root = Path(root_path).resolve()
        if not root.is_dir():
            return []

        gitignore_matcher = GitIgnoreMatcher(root, self.custom_ignore_rules)
        discovered: List[DiscoveredFile] = []

        for dirpath, dirnames, filenames in os.walk(root):
            rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
            if rel_dir == ".":
                rel_dir = ""

            # Prune excluded directories in-place to avoid descending into them
            dirnames[:] = [
                d
                for d in dirnames
                if d not in DEFAULT_EXCLUDED_DIRS
                and not gitignore_matcher.is_ignored(f"{rel_dir}/{d}" if rel_dir else d)
            ]

            for fname in filenames:
                file_ext = os.path.splitext(fname)[1].lower()
                if file_ext in DEFAULT_EXCLUDED_EXTS:
                    continue

                full_file_path = os.path.join(dirpath, fname)
                rel_file_path = os.path.relpath(full_file_path, root).replace("\\", "/")

                if gitignore_matcher.is_ignored(rel_file_path):
                    continue

                try:
                    file_stat = os.stat(full_file_path)
                    size = file_stat.st_size
                except OSError:
                    continue

                is_binary = self._is_binary_file(full_file_path)
                category = self._classify_file(rel_file_path, fname, is_binary)
                language = self._detect_language(rel_file_path, fname)

                # Count lines and compute SHA-256
                lines_count = 0
                sha256_hash = ""
                if not is_binary and size <= self.max_file_size_bytes:
                    sha256_hash, lines_count = self._hash_and_count_lines(full_file_path)
                elif is_binary:
                    sha256_hash = self._hash_binary_file(full_file_path)

                discovered.append(
                    DiscoveredFile(
                        relative_path=rel_file_path,
                        full_path=full_file_path,
                        size_bytes=size,
                        sha256_hash=sha256_hash,
                        language=language,
                        category=category,
                        is_binary=is_binary,
                        lines_count=lines_count,
                    )
                )

        return discovered

    def _is_binary_file(self, file_path: str) -> bool:
        """Checks if a file is binary by scanning first 8KB for null bytes."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(8192)
                return b"\x00" in chunk
        except Exception:
            return True

    def _hash_and_count_lines(self, file_path: str) -> Tuple[str, int]:
        """Calculates SHA-256 and counts text lines."""
        hasher = hashlib.sha256()
        lines_count = 0
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    hasher.update(line.encode("utf-8"))
                    lines_count += 1
            return hasher.hexdigest(), lines_count
        except Exception:
            return "", 0

    def _hash_binary_file(self, file_path: str) -> str:
        """Calculates SHA-256 for a binary file in chunks."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""

    def _detect_language(self, rel_path: str, fname: str) -> Language:
        """Detects programming language from extension and filename."""
        lower_name = fname.lower()
        if lower_name in ("dockerfile", "dockerfile.dev", "dockerfile.prod"):
            return Language.UNKNOWN
        if lower_name.endswith(".d.ts"):
            return Language.TYPESCRIPT

        ext = os.path.splitext(fname)[1].lower()
        return EXTENSION_LANGUAGE_MAP.get(ext, Language.UNKNOWN)

    def _classify_file(self, rel_path: str, fname: str, is_binary: bool) -> FileCategory:
        """Classifies file into architectural roles."""
        if is_binary:
            return FileCategory.ASSET_BINARY

        lower_path = rel_path.lower()
        lower_name = fname.lower()

        # 1. Tests
        if (
            "/tests/" in lower_path
            or "/test/" in lower_path
            or "/__tests__/" in lower_path
            or lower_name.startswith("test_")
            or lower_name.endswith("_test.py")
            or lower_name.endswith(".test.ts")
            or lower_name.endswith(".test.js")
            or lower_name.endswith(".test.tsx")
            or lower_name.endswith(".test.jsx")
            or lower_name.endswith(".spec.ts")
            or lower_name.endswith(".spec.js")
            or lower_name.endswith(".spec.tsx")
            or lower_name.endswith(".spec.jsx")
            or (lower_name.endswith("test.java") or lower_name.endswith("tests.java"))
            or lower_name.endswith("_test.go")
        ):
            return FileCategory.TEST

        # 2. Configuration
        if lower_name in {c.lower() for c in CONFIG_FILENAMES}:
            return FileCategory.CONFIGURATION

        # 3. Documentation
        if (
            lower_name.endswith(".md")
            or lower_name.endswith(".rst")
            or lower_name.startswith("readme")
            or lower_name.startswith("license")
            or lower_name.startswith("contributing")
            or "/docs/" in lower_path
        ):
            return FileCategory.DOCUMENTATION

        # 4. Database migrations
        if "/alembic/" in lower_path or "/migrations/" in lower_path or lower_name.endswith("migration.sql"):
            return FileCategory.DATABASE_MIGRATION

        # 5. Source code
        ext = os.path.splitext(fname)[1].lower()
        if ext in EXTENSION_LANGUAGE_MAP:
            return FileCategory.SOURCE_CODE

        return FileCategory.SOURCE_CODE
