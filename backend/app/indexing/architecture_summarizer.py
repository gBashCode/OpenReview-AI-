"""Repository Architecture Summarization Engine."""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, Dict, List, Set
from app.indexing.dependency_graph import DependencyGraph
from app.indexing.file_discovery import DiscoveredFile, FileCategory, Language


@dataclass
class ArchitectureSummary:
    """Structured architectural overview of a repository."""

    total_files: int
    total_lines_of_code: int
    primary_language: str
    language_breakdown: Dict[str, Dict[str, Any]]
    detected_frameworks: List[str]
    entry_points: List[str]
    core_modules: List[str]
    key_configurations: List[str]
    test_files_count: int
    test_coverage_ratio: float
    project_type: str


class ArchitectureSummarizer:
    """Analyzes discovered files and dependencies to construct architectural intelligence."""

    FRAMEWORK_PATTERNS = {
        # Python
        "FastAPI": ["fastapi", "app.main", "from fastapi import"],
        "SQLAlchemy": ["sqlalchemy", "mapped_column", "declarative_base"],
        "Alembic": ["alembic.ini", "alembic/versions"],
        "Pydantic": ["pydantic", "BaseModel"],
        "Celery": ["celery", "celery_app"],
        "Pytest": ["pytest", "conftest.py"],
        "Django": ["django", "manage.py", "settings.py"],
        "Flask": ["flask", "Flask(__name__)"],
        # JS / TS
        "React": ["react", "react-dom", "useState", "useEffect"],
        "Vite": ["vite.config.ts", "vite.config.js"],
        "Next.js": ["next.config.js", "next.config.mjs", "next/router"],
        "Express": ["express", "express()"],
        "Tailwind CSS": ["tailwind.config.js", "tailwind.config.ts"],
        "Monaco Editor": ["@monaco-editor/react", "monaco-editor"],
        # Java
        "Spring Boot": ["@SpringBootApplication", "org.springframework.boot", "pom.xml"],
        "JUnit": ["org.junit", "@Test"],
        # Go
        "Gin": ["github.com/gin-gonic/gin", "gin.Default()"],
        "Echo": ["github.com/labstack/echo"],
        "Fiber": ["github.com/gofiber/fiber"],
    }

    def summarize(
        self,
        files: List[DiscoveredFile],
        dep_graph: Optional[DependencyGraph] = None,
    ) -> ArchitectureSummary:
        """Generates architectural profile of the repository."""
        total_files = len(files)
        total_loc = sum(f.lines_count for f in files)

        # 1. Language breakdown
        lang_counts: Dict[str, int] = {}
        lang_loc: Dict[str, int] = {}
        for f in files:
            lang_str = f.language.value
            lang_counts[lang_str] = lang_counts.get(lang_str, 0) + 1
            lang_loc[lang_str] = lang_loc.get(lang_str, 0) + f.lines_count

        lang_breakdown: Dict[str, Dict[str, Any]] = {}
        for l_name, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
            loc = lang_loc.get(l_name, 0)
            pct = round((loc / total_loc * 100) if total_loc > 0 else 0, 1)
            lang_breakdown[l_name] = {
                "file_count": count,
                "lines_of_code": loc,
                "percentage": pct,
            }

        primary_lang = "unknown"
        valid_code_langs = [l for l in lang_breakdown if l not in ("unknown", "markdown", "json", "yaml", "toml")]
        if valid_code_langs:
            primary_lang = max(valid_code_langs, key=lambda l: lang_breakdown[l]["lines_of_code"])

        # 2. Key Configurations & Entry Points
        key_configs = [f.relative_path for f in files if f.category == FileCategory.CONFIGURATION]
        test_files = [f for f in files if f.category == FileCategory.TEST]
        source_files = [f for f in files if f.category == FileCategory.SOURCE_CODE]

        entry_points = []
        entry_patterns = {
            "main.py",
            "app/main.py",
            "backend/app/main.py",
            "index.ts",
            "src/main.tsx",
            "src/main.ts",
            "src/index.tsx",
            "src/index.ts",
            "cmd/main.go",
            "main.go",
            "Application.java",
        }
        for f in files:
            rel = f.relative_path.replace("\\", "/")
            if any(rel.endswith(ep) or rel == ep for ep in entry_patterns):
                entry_points.append(rel)

        # 3. Detect Frameworks
        all_rel_paths = {f.relative_path.lower() for f in files}
        detected_frameworks: Set[str] = set()

        for framework, triggers in self.FRAMEWORK_PATTERNS.items():
            for trig in triggers:
                trig_lower = trig.lower()
                # Check path match
                if any(trig_lower in p for p in all_rel_paths):
                    detected_frameworks.add(framework)
                    break
                # Check imports from dependency graph
                if dep_graph and any(trig_lower in imp.lower() for imp in dep_graph.file_imports):
                    detected_frameworks.add(framework)
                    break

        # 4. Core Modules (Top-level directories)
        top_dirs: Set[str] = set()
        for f in source_files:
            parts = f.relative_path.replace("\\", "/").split("/")
            if len(parts) > 1:
                top_dirs.add(parts[0] if len(parts) == 2 else f"{parts[0]}/{parts[1]}")
        core_modules = sorted(list(top_dirs))[:10]

        # 5. Project Type Classification
        has_frontend = any(f.language in (Language.JAVASCRIPT, Language.TYPESCRIPT) for f in files)
        has_backend = any(f.language in (Language.PYTHON, Language.JAVA, Language.GO) for f in files)
        if has_frontend and has_backend:
            project_type = "Full-Stack Monorepo"
        elif has_frontend:
            project_type = "Frontend Web Application"
        elif has_backend:
            project_type = "Backend Microservice / REST API"
        else:
            project_type = "Software Library / Repository"

        # 6. Test coverage ratio
        test_ratio = round((len(test_files) / len(source_files)) if source_files else 0.0, 2)

        return ArchitectureSummary(
            total_files=total_files,
            total_lines_of_code=total_loc,
            primary_language=primary_lang,
            language_breakdown=lang_breakdown,
            detected_frameworks=sorted(list(detected_frameworks)),
            entry_points=sorted(entry_points),
            core_modules=core_modules,
            key_configurations=sorted(key_configs)[:15],
            test_files_count=len(test_files),
            test_coverage_ratio=test_ratio,
            project_type=project_type,
        )
