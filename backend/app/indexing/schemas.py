"""Repository Indexing, Search, Context Retrieval, and Architecture Schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class RepositoryIndexBase(BaseModel):
    repository_id: str
    branch: str = "main"
    commit_sha: str
    status: str = "pending"
    total_files: int = 0
    total_chunks: int = 0
    total_symbols: int = 0


class RepositoryIndexCreate(BaseModel):
    repository_id: Optional[str] = None
    branch: Optional[str] = "main"
    commit_sha: str = "HEAD"
    local_path: Optional[str] = None
    incremental: bool = True


class RepositoryIndexRead(RepositoryIndexBase):
    id: str
    error_message: Optional[str] = None
    indexed_at: Optional[datetime] = None
    summary_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CodeChunkRead(BaseModel):
    id: str
    index_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    token_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CodeSymbolRead(BaseModel):
    id: str
    index_id: str
    name: str
    kind: str
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Search & Retrieval Schemas ---


class SymbolSearchRequest(BaseModel):
    query: str
    kind: Optional[str] = None  # function, class, method, etc.
    file_path: Optional[str] = None
    limit: int = 20


class SymbolSearchResult(BaseModel):
    id: str
    name: str
    kind: str
    file_path: str
    line_number: int
    end_line_number: Optional[int] = None
    signature: Optional[str] = None
    docstring: Optional[str] = None


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 10
    min_similarity: float = 0.2


class SemanticSearchResult(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    content: str
    similarity: float


class ChangedFileItem(BaseModel):
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    changed_lines: Optional[List[int]] = None
    patch: Optional[str] = None


class ContextRetrievalRequest(BaseModel):
    changed_files: List[ChangedFileItem]
    top_k_semantic: int = 5


class SymbolEvidenceDTO(BaseModel):
    name: str
    kind: str
    file_path: str
    line_number: int
    end_line_number: int
    signature: Optional[str] = None
    docstring: Optional[str] = None
    source_code: Optional[str] = None


class CallerEvidenceDTO(BaseModel):
    caller_name: str
    callee_name: str
    file_path: str
    line_number: int
    signature: Optional[str] = None


class ImportEvidenceDTO(BaseModel):
    module: str
    file_path: str
    imported_symbols: List[str] = []


class TestEvidenceDTO(BaseModel):
    test_file_path: str
    target_file_path: str
    test_cases: List[str] = []


class DocEvidenceDTO(BaseModel):
    file_path: str
    title: str
    snippet: str
    line_number: int


class PRContextEvidenceResponse(BaseModel):
    repository_id: str
    commit_sha: str
    changed_symbols: List[SymbolEvidenceDTO]
    enclosing_classes: List[SymbolEvidenceDTO] = []
    function_callers: List[CallerEvidenceDTO] = []
    imported_modules: List[ImportEvidenceDTO] = []
    related_tests: List[TestEvidenceDTO] = []
    relevant_docs: List[DocEvidenceDTO] = []
    semantic_matches: List[SemanticSearchResult] = []


class ArchitectureSummaryResponse(BaseModel):
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


class RelatedFilesResponse(BaseModel):
    file_path: str
    imported_modules: List[str]
    dependent_files: List[str]
    related_tests: List[str]
