"""AST-Aware Semantic Code and Text Chunking Engine."""

from dataclasses import dataclass
from typing import List, Optional
from app.indexing.ast_parser import ParsedSymbol
from app.indexing.file_discovery import Language


@dataclass
class CodeChunkItem:
    """Represents a generated code chunk ready for embedding and database storage."""

    file_path: str
    start_line: int  # 1-indexed
    end_line: int  # 1-indexed
    content: str
    token_count: int
    chunk_type: str  # symbol, preamble, sliding_window


class SemanticChunker:
    """Chunks source code and documentation semantically preserving syntactic boundaries."""

    def __init__(
        self,
        max_chunk_lines: int = 80,
        chunk_overlap_lines: int = 15,
        target_token_limit: int = 500,
    ):
        self.max_chunk_lines = max_chunk_lines
        self.chunk_overlap_lines = chunk_overlap_lines
        self.target_token_limit = target_token_limit

    def chunk_file(
        self,
        file_path: str,
        content: str,
        symbols: Optional[List[ParsedSymbol]] = None,
        language: Language = Language.UNKNOWN,
    ) -> List[CodeChunkItem]:
        """Generates semantic chunks for a file using AST symbols or sliding windows."""
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)
        if total_lines == 0:
            return []

        chunks: List[CodeChunkItem] = []

        # If AST symbols are available for this file, use symbol-guided chunking
        if symbols:
            # Sort symbols by start_line
            sorted_symbols = sorted(symbols, key=lambda s: (s.line_number, -s.end_line_number))
            
            # Preamble chunk (imports, license, module docstring)
            first_symbol_line = sorted_symbols[0].line_number
            if first_symbol_line > 1:
                preamble_content = "".join(lines[0 : first_symbol_line - 1])
                if preamble_content.strip():
                    chunks.append(
                        CodeChunkItem(
                            file_path=file_path,
                            start_line=1,
                            end_line=first_symbol_line - 1,
                            content=preamble_content.strip(),
                            token_count=self._estimate_tokens(preamble_content),
                            chunk_type="preamble",
                        )
                    )

            # Symbol chunks
            for sym in sorted_symbols:
                s_start = max(1, sym.line_number)
                s_end = min(total_lines, sym.end_line_number)
                sym_lines = lines[s_start - 1 : s_end]
                sym_content = "".join(sym_lines)

                # If symbol is within max size limit, emit directly
                if (s_end - s_start + 1) <= self.max_chunk_lines:
                    chunks.append(
                        CodeChunkItem(
                            file_path=file_path,
                            start_line=s_start,
                            end_line=s_end,
                            content=sym_content.strip(),
                            token_count=self._estimate_tokens(sym_content),
                            chunk_type=f"symbol:{sym.kind}",
                        )
                    )
                else:
                    # Partition large symbol with sliding window preserving header
                    header = sym_lines[0].strip() if sym_lines else sym.name
                    step = self.max_chunk_lines - self.chunk_overlap_lines
                    for w_start in range(s_start, s_end + 1, step):
                        w_end = min(s_end, w_start + self.max_chunk_lines - 1)
                        sub_content = f"// Context: {header}\n" + "".join(lines[w_start - 1 : w_end])
                        chunks.append(
                            CodeChunkItem(
                                file_path=file_path,
                                start_line=w_start,
                                end_line=w_end,
                                content=sub_content.strip(),
                                token_count=self._estimate_tokens(sub_content),
                                chunk_type=f"symbol:{sym.kind}:partition",
                            )
                        )
                        if w_end >= s_end:
                            break

        # Fallback to sliding window for files without parsed AST symbols
        if not chunks:
            step = max(1, self.max_chunk_lines - self.chunk_overlap_lines)
            for w_start in range(1, total_lines + 1, step):
                w_end = min(total_lines, w_start + self.max_chunk_lines - 1)
                chunk_slice = "".join(lines[w_start - 1 : w_end])
                if chunk_slice.strip():
                    chunks.append(
                        CodeChunkItem(
                            file_path=file_path,
                            start_line=w_start,
                            end_line=w_end,
                            content=chunk_slice.strip(),
                            token_count=self._estimate_tokens(chunk_slice),
                            chunk_type="sliding_window",
                        )
                    )
                if w_end >= total_lines:
                    break

        return chunks

    def _estimate_tokens(self, text: str) -> int:
        """Approximates token count based on whitespace and punctuation tokens."""
        # Standard code heuristic: ~3.5 to 4 characters per token
        return max(1, len(text) // 4)
