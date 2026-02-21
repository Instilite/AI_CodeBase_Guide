import os
import re
from pathlib import Path

from constants import ALLOWED_EXTENSIONS, EXCLUDED_DIRNAMES


def grep_function_references(repo_path: Path, function_name: str) -> dict[str, list[int]]:
    escaped_name = re.escape(function_name)
    pattern = re.compile(rf"\b{escaped_name}\b")

    matches: dict[str, list[int]] = {}

    try:
        for root, dirnames, filenames in os.walk(repo_path):
            dirnames[:] = [dirname for dirname in dirnames if dirname not in EXCLUDED_DIRNAMES]
            root_path = Path(root)

            for filename in filenames:
                file_path = root_path / filename
                if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
                    continue

                try:
                    line_numbers: list[int] = []
                    with file_path.open("r", encoding="utf-8", errors="ignore") as file_handle:
                        for idx, line in enumerate(file_handle, start=1):
                            if pattern.search(line):
                                line_numbers.append(idx)

                    if line_numbers:
                        relative_path = str(file_path.relative_to(repo_path))
                        matches[relative_path] = line_numbers
                except Exception:
                    continue
    except Exception:
        return {}

    return matches


def find_definition_file(
    repo_path: Path, all_matches: dict[str, list[int]], function_name: str
) -> str | None:
    escaped_name = re.escape(function_name)
    definition_pattern = re.compile(
        rf"(def|async\s+def|function\s*\*?|const|let|var|class|"
        rf"export\s+const|export\s+default\s+function|export\s+async\s+function|"
        rf"module\.exports)\s*=?\s*{escaped_name}\b"
    )

    for relative_path in sorted(all_matches.keys()):
        file_path = repo_path / relative_path
        try:
            with file_path.open("r", encoding="utf-8", errors="ignore") as file_handle:
                for line in file_handle:
                    if definition_pattern.search(line):
                        return relative_path
        except Exception:
            continue

    return None


def build_grep_chunks(
    all_matches: dict[str, list[int]], files_referencing: list[str], function_name: str
) -> list[dict]:
    chunks: list[dict] = []
    for file_path in files_referencing:
        lines = all_matches.get(file_path, [])
        if not lines:
            continue

        start_line = min(lines)
        end_line = max(lines)
        sampled_lines = ", ".join(str(line) for line in lines[:10])
        text = f"Function '{function_name}' referenced at line(s): {sampled_lines}."
        chunks.append(
            {
                "chunk_id": "",
                "file_path": file_path,
                "start_line": start_line,
                "end_line": end_line,
                "text": text,
                "similarity": None,
            }
        )
    return chunks
