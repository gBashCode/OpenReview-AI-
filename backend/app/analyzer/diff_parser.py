"""Unified Git Diff Parser Engine.

Parses multi-file Git diffs into structured files, hunks, additions, deletions,
and exact line numbers for precise AST symbol mapping and inline review comments.
"""

from dataclasses import dataclass, field
import os
import re
from typing import List, Optional, Tuple

from app.analyzer.schemas import ChangedFileDTO, DiffHunkDTO, DiffLineItem
from app.indexing.file_discovery import FileDiscoveryService


@dataclass
class ParsedDiffFile:
    """Internal model for a parsed file inside a unified diff."""

    old_path: Optional[str]
    new_path: str
    status: str  # "modified", "added", "deleted", "renamed"
    additions: int = 0
    deletions: int = 0
    added_lines: List[Tuple[int, str]] = field(default_factory=list)  # (new_line, text)
    removed_lines: List[Tuple[int, str]] = field(default_factory=list)  # (old_line, text)
    modified_line_numbers: List[int] = field(default_factory=list)  # new line numbers
    hunks: List[DiffHunkDTO] = field(default_factory=list)
    raw_patch: str = ""


class UnifiedDiffParser:
    """Parses raw unified Git diff text into rich, typed file diff structures."""

    HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: ?(.*))?")

    def __init__(self):
        self.discovery_service = FileDiscoveryService()

    def parse(self, raw_diff: str) -> List[ParsedDiffFile]:
        """Parses a multi-file unified git diff string."""
        if not raw_diff or not raw_diff.strip():
            return []

        files: List[ParsedDiffFile] = []
        lines = raw_diff.splitlines()
        idx = 0
        total_lines = len(lines)

        while idx < total_lines:
            line = lines[idx]

            # Detect file boundary: "diff --git a/... b/..."
            if line.startswith("diff --git "):
                match = re.match(r"^diff --git a/(.*) b/(.*)$", line)
                if match:
                    old_path = match.group(1).strip()
                    new_path = match.group(2).strip()
                else:
                    parts = line.split(" ")
                    old_path = parts[2][2:] if len(parts) > 2 else "unknown"
                    new_path = parts[3][2:] if len(parts) > 3 else "unknown"

                idx += 1
                status = "modified"
                patch_lines = [line]

                # Parse file headers until hunks or next file
                while idx < total_lines and not lines[idx].startswith("@@") and not lines[idx].startswith("diff --git "):
                    sub_line = lines[idx]
                    patch_lines.append(sub_line)
                    if sub_line.startswith("new file mode"):
                        status = "added"
                    elif sub_line.startswith("deleted file mode"):
                        status = "deleted"
                    elif sub_line.startswith("rename from"):
                        status = "renamed"
                    elif sub_line.startswith("--- /dev/null"):
                        status = "added"
                    elif sub_line.startswith("+++ /dev/null"):
                        status = "deleted"
                    idx += 1

                # Parse hunks for this file
                hunks: List[DiffHunkDTO] = []
                added_lines: List[Tuple[int, str]] = []
                removed_lines: List[Tuple[int, str]] = []
                modified_lines: List[int] = []

                while idx < total_lines and not lines[idx].startswith("diff --git "):
                    hunk_line = lines[idx]
                    hunk_match = self.HUNK_HEADER_RE.match(hunk_line)
                    if not hunk_match:
                        # Non-hunk line within file diff (e.g. index/mode)
                        patch_lines.append(hunk_line)
                        idx += 1
                        continue

                    patch_lines.append(hunk_line)
                    old_start = int(hunk_match.group(1))
                    old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                    new_start = int(hunk_match.group(3))
                    new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                    heading = hunk_match.group(5).strip() if hunk_match.group(5) else None

                    current_old = old_start
                    current_new = new_start
                    hunk_items: List[DiffLineItem] = []
                    idx += 1

                    # Process lines in current hunk
                    while idx < total_lines and not lines[idx].startswith("@@") and not lines[idx].startswith("diff --git "):
                        dl = lines[idx]
                        patch_lines.append(dl)

                        if dl.startswith("+"):
                            text = dl[1:]
                            added_lines.append((current_new, text))
                            modified_lines.append(current_new)
                            hunk_items.append(
                                DiffLineItem(
                                    line_type="+",
                                    old_line_number=None,
                                    new_line_number=current_new,
                                    content=text,
                                )
                            )
                            current_new += 1
                        elif dl.startswith("-"):
                            text = dl[1:]
                            removed_lines.append((current_old, text))
                            # Add anchor line in new revision for context
                            modified_lines.append(max(1, current_new))
                            hunk_items.append(
                                DiffLineItem(
                                    line_type="-",
                                    old_line_number=current_old,
                                    new_line_number=None,
                                    content=text,
                                )
                            )
                            current_old += 1
                        elif dl.startswith(" "):
                            text = dl[1:]
                            hunk_items.append(
                                DiffLineItem(
                                    line_type=" ",
                                    old_line_number=current_old,
                                    new_line_number=current_new,
                                    content=text,
                                )
                            )
                            current_old += 1
                            current_new += 1
                        elif dl.startswith("\\"):
                            # "\ No newline at end of file"
                            pass
                        idx += 1

                    hunks.append(
                        DiffHunkDTO(
                            old_start=old_start,
                            old_lines=old_count,
                            new_start=new_start,
                            new_lines=new_count,
                            heading=heading,
                            lines=hunk_items,
                        )
                    )

                files.append(
                    ParsedDiffFile(
                        old_path=old_path if status != "added" else None,
                        new_path=new_path if status != "deleted" else old_path,
                        status=status,
                        additions=len(added_lines),
                        deletions=len(removed_lines),
                        added_lines=added_lines,
                        removed_lines=removed_lines,
                        modified_line_numbers=sorted(list(set(modified_lines))),
                        hunks=hunks,
                        raw_patch="\n".join(patch_lines),
                    )
                )
            else:
                idx += 1

        return files

    def to_dto(self, parsed_file: ParsedDiffFile) -> ChangedFileDTO:
        """Converts internal ParsedDiffFile to API ChangedFileDTO with classifications."""
        fname = os.path.basename(parsed_file.new_path)
        lang = self.discovery_service._detect_language(parsed_file.new_path, fname)
        cat = self.discovery_service._classify_file(parsed_file.new_path, fname, is_binary=False)

        return ChangedFileDTO(
            file_path=parsed_file.new_path.replace("\\", "/"),
            old_path=parsed_file.old_path.replace("\\", "/") if parsed_file.old_path else None,
            status=parsed_file.status,
            additions=parsed_file.additions,
            deletions=parsed_file.deletions,
            language=lang.value,
            category=cat.value,
            modified_line_numbers=parsed_file.modified_line_numbers,
            patch=parsed_file.raw_patch,
        )
