"""Comprehensive Tests for OpenReview AI Repository Intelligence Engine.

Covers:
1. Multi-language Tree-sitter AST extraction (Python, JS, TS, Java, Go)
2. File discovery, .gitignore evaluation, binary detection, classification
3. Semantic code chunking & token calculation
4. 1536-dimensional deterministic embedding generation & vector properties
5. Dependency graph resolution (imports, call graph, test mappings)
6. Repository architecture summarization
7. Initial & incremental repository indexing
8. Hybrid PR context retrieval (changed functions, callers, tests, documentation)
9. Repository Intelligence REST APIs
"""

import json
import math
import os
import shutil
import tempfile
import pytest
from httpx import AsyncClient

from app.indexing.architecture_summarizer import ArchitectureSummarizer
from app.indexing.ast_parser import TreeSitterASTParser
from app.indexing.chunker import SemanticChunker
from app.indexing.context_retriever import ContextRetriever
from app.indexing.dependency_graph import DependencyGraph
from app.indexing.embeddings import DeterministicEmbeddingProvider
from app.indexing.file_discovery import DiscoveredFile, FileCategory, FileDiscoveryService, Language
from app.indexing.repository_indexer import RepositoryIndexer


# =============================================================================
# 1. TREE-SITTER AST PARSER TESTS FOR 5 LANGUAGES
# =============================================================================

def test_ast_parser_python():
    parser = TreeSitterASTParser()
    code = """
import os
from datetime import datetime

class AuthenticationService:
    \"\"\"Handles user authentication and token creation.\"\"\"
    def __init__(self, secret: str):
        self.secret = secret

    def authenticate(self, user: str, token: str) -> bool:
        if not user:
            return False
        return self.verify_token(token)

    def verify_token(self, token: str) -> bool:
        return len(token) > 10
"""
    symbols, imports = parser.parse_file("auth.py", code, Language.PYTHON)
    
    # Check imports
    assert len(imports) >= 2
    assert any(i.module == "os" for i in imports)
    assert any(i.module == "datetime" and "datetime" in i.imported_names for i in imports)

    # Check class
    classes = [s for s in symbols if s.kind == "class"]
    assert len(classes) == 1
    assert classes[0].name == "AuthenticationService"
    assert "Handles user authentication" in (classes[0].docstring or "")

    # Check methods & call graph
    methods = [s for s in symbols if s.kind == "method"]
    method_names = {m.name for m in methods}
    assert "authenticate" in method_names
    assert "verify_token" in method_names

    auth_method = next(m for m in methods if m.name == "authenticate")
    assert "verify_token" in auth_method.calls
    assert auth_method.parent_symbol == "AuthenticationService"


def test_ast_parser_javascript_and_typescript():
    parser = TreeSitterASTParser()

    # TypeScript with interface and class
    ts_code = """
import { Logger } from './logger';

export interface User {
    id: string;
    username: string;
}

export class UserService implements User {
    id: string;
    username: string;

    constructor(id: string, username: string) {
        this.id = id;
        this.username = username;
    }

    findUser(userId: string): User | null {
        Logger.info(userId);
        return null;
    }
}

export const helperFunction = (val: string) => {
    return val.toUpperCase();
};
"""
    symbols, imports = parser.parse_file("user.ts", ts_code, Language.TYPESCRIPT)
    assert len(imports) == 1
    assert imports[0].module == "./logger"

    sym_names = {s.name: s for s in symbols}
    assert "User" in sym_names and sym_names["User"].kind == "interface"
    assert "UserService" in sym_names and sym_names["UserService"].kind == "class"
    assert "findUser" in sym_names and sym_names["findUser"].kind == "method"
    assert "helperFunction" in sym_names and sym_names["helperFunction"].kind == "function"
    assert "info" in sym_names["findUser"].calls


def test_ast_parser_java():
    parser = TreeSitterASTParser()
    java_code = """
package com.openreview.service;

import java.util.List;
import com.openreview.model.Order;

public class OrderService {
    public void processOrder(String orderId) {
        validateOrder(orderId);
        System.out.println("Processed " + orderId);
    }

    private boolean validateOrder(String id) {
        return id != null && !id.isEmpty();
    }
}
"""
    symbols, imports = parser.parse_file("OrderService.java", java_code, Language.JAVA)
    assert any("com.openreview.model.Order" in i.module for i in imports)

    classes = [s for s in symbols if s.kind == "class"]
    assert len(classes) == 1
    assert classes[0].name == "OrderService"

    methods = {s.name: s for s in symbols if s.kind == "method"}
    assert "processOrder" in methods
    assert "validateOrder" in methods
    assert "validateOrder" in methods["processOrder"].calls


def test_ast_parser_go():
    parser = TreeSitterASTParser()
    go_code = """
package main

import (
    "fmt"
    "net/http"
)

type ServerConfig struct {
    Port int
}

func (s *ServerConfig) StartServer() error {
    fmt.Println(s.Port)
    return nil
}

func CreateServer(port int) *ServerConfig {
    return &ServerConfig{Port: port}
}
"""
    symbols, imports = parser.parse_file("server.go", go_code, Language.GO)
    import_mods = {i.module for i in imports}
    assert "fmt" in import_mods
    assert "net/http" in import_mods

    sym_dict = {s.name: s for s in symbols}
    assert "ServerConfig" in sym_dict and sym_dict["ServerConfig"].kind == "struct"
    assert "StartServer" in sym_dict and sym_dict["StartServer"].kind == "method"
    assert sym_dict["StartServer"].parent_symbol == "ServerConfig"
    assert "CreateServer" in sym_dict and sym_dict["CreateServer"].kind == "function"


# =============================================================================
# 2. FILE DISCOVERY, GITIGNORE, AND CLASSIFICATION
# =============================================================================

def test_file_discovery_and_classification(tmp_path):
    # Setup mock repository directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("def main(): pass", encoding="utf-8")
    (tmp_path / "src" / "utils.ts").write_text("export const a = 1;", encoding="utf-8")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("def test_main(): assert True", encoding="utf-8")

    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "architecture.md").write_text("# Architecture", encoding="utf-8")

    # Config file
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'", encoding="utf-8")

    # Ignored directory & file
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("console.log()", encoding="utf-8")

    # Binary file
    (tmp_path / "sample.dat").write_bytes(b"\x00\x01\x02\x03\x04")

    # Gitignore
    (tmp_path / ".gitignore").write_text("*.log\nsecret_dir/\n", encoding="utf-8")
    (tmp_path / "app.log").write_text("error log", encoding="utf-8")

    discovery = FileDiscoveryService()
    files = discovery.discover_repository(str(tmp_path))
    paths = {f.relative_path: f for f in files}

    # Verify exclusions
    assert not any("node_modules" in p for p in paths)
    assert not any("app.log" in p for p in paths)

    # Verify inclusions & classifications
    assert "src/main.py" in paths
    assert paths["src/main.py"].category == FileCategory.SOURCE_CODE
    assert paths["src/main.py"].language == Language.PYTHON
    assert len(paths["src/main.py"].sha256_hash) == 64

    assert "src/utils.ts" in paths
    assert paths["src/utils.ts"].language == Language.TYPESCRIPT

    assert "tests/test_main.py" in paths
    assert paths["tests/test_main.py"].category == FileCategory.TEST

    assert "pyproject.toml" in paths
    assert paths["pyproject.toml"].category == FileCategory.CONFIGURATION

    assert "docs/architecture.md" in paths
    assert paths["docs/architecture.md"].category == FileCategory.DOCUMENTATION

    assert "sample.dat" in paths
    assert paths["sample.dat"].is_binary is True
    assert paths["sample.dat"].category == FileCategory.ASSET_BINARY


# =============================================================================
# 3. SEMANTIC CODE CHUNKING
# =============================================================================

def test_semantic_code_chunker():
    chunker = SemanticChunker(max_chunk_lines=50)
    code = """# Module header preamble
import os

def calculate_discount(price: float, discount: float) -> float:
    \"\"\"Calculates discount with validation.\"\"\"
    if price < 0:
        raise ValueError("Price cannot be negative")
    return price * (1.0 - discount)

class OrderCalculator:
    def total(self, items):
        return sum(items)
"""
    parser = TreeSitterASTParser()
    symbols, _ = parser.parse_file("calc.py", code, Language.PYTHON)

    chunks = chunker.chunk_file("calc.py", code, symbols=symbols, language=Language.PYTHON)
    assert len(chunks) >= 2

    # Check that functions and classes are emitted with boundaries
    calc_chunk = next(c for c in chunks if "calculate_discount" in c.content)
    assert calc_chunk.start_line >= 4
    assert calc_chunk.end_line <= 9
    assert calc_chunk.token_count > 0
    assert "symbol:function" in calc_chunk.chunk_type


# =============================================================================
# 4. DETERMINISTIC 1536-DIM EMBEDDINGS
# =============================================================================

@pytest.mark.asyncio
async def test_deterministic_embedding_provider():
    provider = DeterministicEmbeddingProvider(dimension=1536)

    text_auth = "def verify_jwt_bearer_token(secret, token): pass"
    text_auth_similar = "def validate_jwt_token(secret, token): pass"
    text_unrelated = "func CalculateMatrixDeterminant(m [][]float64) float64"

    vec1 = await provider.embed_query(text_auth)
    vec2 = await provider.embed_query(text_auth_similar)
    vec3 = await provider.embed_query(text_unrelated)

    # 1. Dimension check
    assert len(vec1) == 1536
    assert len(vec2) == 1536
    assert len(vec3) == 1536

    # 2. L2 Normalization check (norm == 1.0)
    norm1 = math.sqrt(sum(x * x for x in vec1))
    assert pytest.approx(norm1, rel=1e-4) == 1.0

    # 3. Determinism
    vec1_again = await provider.embed_query(text_auth)
    assert vec1 == vec1_again

    # 4. Semantic similarity: auth and auth_similar should have higher cosine similarity than unrelated
    sim_similar = sum(a * b for a, b in zip(vec1, vec2))
    sim_unrelated = sum(a * b for a, b in zip(vec1, vec3))
    assert sim_similar > sim_unrelated


# =============================================================================
# 5. DEPENDENCY GRAPH AND CALL GRAPH
# =============================================================================

def test_dependency_graph_and_callers():
    graph = DependencyGraph()

    # File 1: auth.py
    from app.indexing.ast_parser import ParsedImport, ParsedSymbol
    sym_login = ParsedSymbol(
        name="login",
        kind="function",
        file_path="src/auth.py",
        line_number=10,
        end_line_number=20,
        calls=["verify_password"],
    )
    sym_verify = ParsedSymbol(
        name="verify_password",
        kind="function",
        file_path="src/auth.py",
        line_number=22,
        end_line_number=30,
        calls=[],
    )
    graph.add_symbols("src/auth.py", [sym_login, sym_verify])
    graph.add_imports("src/auth.py", [ParsedImport(module="src.utils")])

    # File 2: api.py calling login
    sym_route = ParsedSymbol(
        name="login_route",
        kind="function",
        file_path="src/api.py",
        line_number=5,
        end_line_number=15,
        calls=["login"],
    )
    graph.add_symbols("src/api.py", [sym_route])

    # Resolve
    fake_files = [
        DiscoveredFile("src/auth.py", "src/auth.py", 100, "h1", Language.PYTHON, FileCategory.SOURCE_CODE, False),
        DiscoveredFile("src/api.py", "src/api.py", 100, "h2", Language.PYTHON, FileCategory.SOURCE_CODE, False),
        DiscoveredFile("tests/test_auth.py", "tests/test_auth.py", 100, "h3", Language.PYTHON, FileCategory.TEST, False),
    ]
    graph.resolve_relationships(fake_files)

    # 1. Callers of login
    callers = graph.get_callers("login")
    assert "login_route" in callers

    # 2. Callers of verify_password
    v_callers = graph.get_callers("verify_password")
    assert "login" in v_callers

    # 3. Test mappings
    related_tests = graph.get_related_tests("src/auth.py")
    assert "tests/test_auth.py" in related_tests


# =============================================================================
# 6. ARCHITECTURE SUMMARIZER
# =============================================================================

def test_architecture_summarizer():
    summarizer = ArchitectureSummarizer()
    files = [
        DiscoveredFile("backend/app/main.py", "", 1000, "h1", Language.PYTHON, FileCategory.SOURCE_CODE, False, lines_count=120),
        DiscoveredFile("backend/app/auth/service.py", "", 2000, "h2", Language.PYTHON, FileCategory.SOURCE_CODE, False, lines_count=180),
        DiscoveredFile("frontend/src/App.tsx", "", 1500, "h3", Language.TYPESCRIPT, FileCategory.SOURCE_CODE, False, lines_count=90),
        DiscoveredFile("pyproject.toml", "", 500, "h4", Language.TOML, FileCategory.CONFIGURATION, False, lines_count=30),
        DiscoveredFile("tests/test_auth.py", "", 800, "h5", Language.PYTHON, FileCategory.TEST, False, lines_count=50),
    ]

    summary = summarizer.summarize(files)
    assert summary.total_files == 5
    assert summary.total_lines_of_code == 470
    assert summary.primary_language == "python"
    assert "backend/app/main.py" in summary.entry_points
    assert summary.project_type == "Full-Stack Monorepo"
    assert summary.test_files_count == 1


# =============================================================================
# 7. INITIAL & INCREMENTAL REPOSITORY INDEXING WORKFLOW
# =============================================================================

@pytest.mark.asyncio
async def test_full_and_incremental_indexing_workflow(async_client: AsyncClient, tmp_path):
    # Create sample repository files
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "service.py").write_text(
        "def compute_total(price: float) -> float:\n    return price * 1.15\n",
        encoding="utf-8",
    )
    (repo_dir / "test_service.py").write_text(
        "from service import compute_total\ndef test_total():\n    assert compute_total(10) > 10\n",
        encoding="utf-8",
    )

    # 1. Register repo
    reg_res = await async_client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 887766,
            "owner": "deepmind",
            "name": "sample-repo",
            "default_branch": "main",
        },
    )
    assert reg_res.status_code == 201
    repo_id = reg_res.json()["id"]

    # 2. Perform Initial Index
    idx1_res = await async_client.post(
        f"/api/v1/repositories/{repo_id}/indexes",
        json={
            "commit_sha": "c00112233445566778899aabbccddeeff0011223",
            "local_path": str(repo_dir),
            "incremental": True,
        },
    )
    assert idx1_res.status_code == 201
    idx1_data = idx1_res.json()
    assert idx1_data["status"] == "completed"
    assert idx1_data["total_files"] >= 2
    assert idx1_data["total_chunks"] >= 2
    assert idx1_data["total_symbols"] >= 2

    # 3. Modify service.py & add new_module.py for Incremental Index
    (repo_dir / "service.py").write_text(
        "def compute_total(price: float) -> float:\n    # updated with tax\n    tax = 0.20\n    return price * (1.0 + tax)\n",
        encoding="utf-8",
    )
    (repo_dir / "new_module.py").write_text(
        "def format_currency(amount: float) -> str:\n    return f'${amount:.2f}'\n",
        encoding="utf-8",
    )

    idx2_res = await async_client.post(
        f"/api/v1/repositories/{repo_id}/indexes",
        json={
            "commit_sha": "c99887766554433221100ffeeddccbbaa9988776",
            "local_path": str(repo_dir),
            "incremental": True,
        },
    )
    assert idx2_res.status_code == 201
    idx2_data = idx2_res.json()
    assert idx2_data["status"] == "completed"
    assert idx2_data["total_files"] >= 3


# =============================================================================
# 8. HYBRID CONTEXT RETRIEVAL FOR PR REVIEWS
# =============================================================================

@pytest.mark.asyncio
async def test_pr_hybrid_context_retrieval(async_client: AsyncClient, tmp_path):
    repo_dir = tmp_path / "pr_context_repo"
    repo_dir.mkdir()
    
    # 1. Main service
    (repo_dir / "order_service.py").write_text(
        """class OrderManager:
    \"\"\"Manages order operations.\"\"\"
    def process_order(self, order_id: str) -> bool:
        if not order_id:
            return False
        return self.save_order(order_id)

    def save_order(self, order_id: str) -> bool:
        return True
""",
        encoding="utf-8",
    )
    # 2. Caller file
    (repo_dir / "api_handler.py").write_text(
        """from order_service import OrderManager

def handle_checkout(order_id: str):
    mgr = OrderManager()
    return mgr.process_order(order_id)
""",
        encoding="utf-8",
    )
    # 3. Test file
    (repo_dir / "test_order_service.py").write_text(
        """from order_service import OrderManager

def test_process_order():
    mgr = OrderManager()
    assert mgr.process_order("ord-123") is True
""",
        encoding="utf-8",
    )
    # 4. Docs
    (repo_dir / "README.md").write_text(
        "# Order Service\nDetailed documentation for process_order and OrderManager lifecycle.\n",
        encoding="utf-8",
    )

    # Register & Index
    repo_res = await async_client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 334455,
            "owner": "deepmind",
            "name": "pr-context-repo",
            "default_branch": "main",
        },
    )
    repo_id = repo_res.json()["id"]

    idx_res = await async_client.post(
        f"/api/v1/repositories/{repo_id}/indexes",
        json={
            "commit_sha": "d00112233445566778899aabbccddeeff0011223",
            "local_path": str(repo_dir),
        },
    )
    assert idx_res.status_code == 201

    # 5. Execute Context Retrieval for PR changing process_order (lines 3-6)
    ctx_res = await async_client.post(
        f"/api/v1/repositories/{repo_id}/context",
        json={
            "changed_files": [
                {
                    "file_path": "order_service.py",
                    "changed_lines": [3, 4, 5],
                }
            ],
            "top_k_semantic": 3,
        },
    )
    assert ctx_res.status_code == 200
    ctx_data = ctx_res.json()

    # Verify real source evidence:
    # A. Changed symbol
    changed_syms = ctx_data["changed_symbols"]
    assert len(changed_syms) >= 1
    assert any(s["name"] == "process_order" for s in changed_syms)
    proc_order = next(s for s in changed_syms if s["name"] == "process_order")
    assert proc_order["file_path"] == "order_service.py"
    assert proc_order["line_number"] >= 3

    # B. Function callers
    callers = ctx_data["function_callers"]
    assert len(callers) >= 1
    assert any("handle_checkout" in c["caller_name"] for c in callers)

    # C. Related tests
    tests = ctx_data["related_tests"]
    assert len(tests) >= 1
    assert any("test_order_service.py" in t["test_file_path"] for t in tests)

    # D. Relevant documentation
    docs = ctx_data["relevant_docs"]
    assert len(docs) >= 1
    assert any("README.md" in d["file_path"] for d in docs)


# =============================================================================
# 9. REPOSITORY INTELLIGENCE REST APIS
# =============================================================================

@pytest.mark.asyncio
async def test_intelligence_rest_apis(async_client: AsyncClient, tmp_path):
    repo_dir = tmp_path / "api_test_repo"
    repo_dir.mkdir()
    (repo_dir / "math_utils.py").write_text(
        "def calculate_square_root(n: float) -> float:\n    \"\"\"Calculates square root.\"\"\"\n    return n ** 0.5\n",
        encoding="utf-8",
    )

    reg_res = await async_client.post(
        "/api/v1/repositories",
        json={
            "github_repo_id": 776655,
            "owner": "octocat",
            "name": "intelligence-api-repo",
            "default_branch": "main",
        },
    )
    repo_id = reg_res.json()["id"]

    # Index
    await async_client.post(
        f"/api/v1/repositories/{repo_id}/indexes",
        json={"commit_sha": "abc1234567890abcdef1234567890abcdef12345", "local_path": str(repo_dir)},
    )

    # 1. Symbol Search API
    sym_res = await async_client.get(f"/api/v1/repositories/{repo_id}/symbols?query=calculate_square_root")
    assert sym_res.status_code == 200
    symbols = sym_res.json()
    assert len(symbols) >= 1
    assert symbols[0]["name"] == "calculate_square_root"
    assert symbols[0]["kind"] == "function"

    # 2. Semantic Search API
    sem_res = await async_client.post(
        f"/api/v1/repositories/{repo_id}/search",
        json={"query": "square root math function", "top_k": 5},
    )
    assert sem_res.status_code == 200
    chunks = sem_res.json()
    assert len(chunks) >= 1
    assert "calculate_square_root" in chunks[0]["content"]

    # 3. Architecture Summary API
    arch_res = await async_client.get(f"/api/v1/repositories/{repo_id}/architecture")
    assert arch_res.status_code == 200
    arch = arch_res.json()
    assert arch["total_files"] >= 1
    assert arch["primary_language"] == "python"

    # 4. Related Files API
    rel_res = await async_client.get(
        f"/api/v1/repositories/{repo_id}/related-files?file_path=math_utils.py"
    )
    assert rel_res.status_code == 200
    rel_data = rel_res.json()
    assert rel_data["file_path"] == "math_utils.py"
