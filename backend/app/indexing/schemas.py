"""Repository Indexing and Code Symbols Pydantic schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


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
    commit_sha: str


class RepositoryIndexRead(RepositoryIndexBase):
    id: str
    error_message: Optional[str] = None
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
