from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ingest import ALLOWED_EXTENSIONS, should_skip_path


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _iter_source_files(repo_root: Path) -> List[Path]:
    files: List[Path] = []
    for file_path in sorted(repo_root.rglob("*")):
        if not file_path.is_file():
            continue
        rel = file_path.relative_to(repo_root)
        if should_skip_path(rel):
            continue
        if file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue
        files.append(file_path)
    return files


def find_matching_files(repo_root: Path, function_name: str) -> Tuple[re.Pattern[str], Dict[str, List[int]]]:
    pattern = re.compile(r"\b" + re.escape(function_name) + r"\b")
    matches: Dict[str, List[int]] = {}

    for file_path in _iter_source_files(repo_root):
        rel = file_path.relative_to(repo_root).as_posix()
        text = _read_text(file_path)
        lines = text.splitlines()

        line_hits: List[int] = []
        for i, line in enumerate(lines):
            if pattern.search(line):
                line_hits.append(i)

        if line_hits:
            matches[rel] = line_hits

    return pattern, matches


def _definition_patterns(name: str) -> List[re.Pattern[str]]:
    escaped = re.escape(name)
    return [
        re.compile(rf"^\s*def\s+{escaped}\s*\("),
        re.compile(rf"^\s*class\s+{escaped}\s*[\(:]"),
        re.compile(rf"^\s*function\s+{escaped}\s*\("),
        re.compile(rf"^\s*(export\s+)?(const|let|var)\s+{escaped}\s*=\s*(async\s*)?\("),
        re.compile(rf"^\s*(export\s+default\s+)?class\s+{escaped}\b"),
    ]


def _first_definition_line(file_path: Path, patterns: List[re.Pattern[str]]) -> Optional[int]:
    lines = _read_text(file_path).splitlines()
    for i, line in enumerate(lines):
        for pattern in patterns:
            if pattern.search(line):
                return i
    return None


def find_definition_file(
    repo_root: Path,
    matching_files: Set[str],
    function_name: str,
) -> Optional[str]:
    patterns = _definition_patterns(function_name)

    def choose(candidates: List[str]) -> Optional[str]:
        scored: List[Tuple[int, int, str]] = []
        for rel_path in candidates:
            first_line = _first_definition_line(repo_root / rel_path, patterns)
            if first_line is None:
                continue
            scored.append((first_line, len(rel_path), rel_path))
        if not scored:
            return None
        scored.sort(key=lambda row: (row[0], row[1], row[2]))
        return scored[0][2]

    all_candidates = sorted(matching_files)
    with_filter = [
        path
        for path in all_candidates
        if "test" not in path.lower() and "mock" not in path.lower() and "stub" not in path.lower()
    ]

    selected = choose(with_filter)
    if selected is not None:
        return selected

    return choose(all_candidates)


def build_grep_chunks(
    repo_root: Path,
    matches_by_file: Dict[str, List[int]],
    referencing_files: List[str],
) -> List[Dict[str, object]]:
    grep_chunks: List[Dict[str, object]] = []

    for rel_path in sorted(referencing_files):
        file_path = repo_root / rel_path
        lines = _read_text(file_path).splitlines()
        match_lines = matches_by_file.get(rel_path, [])[:2]

        for match_line in match_lines:
            start = max(0, match_line - 10)
            end = min(len(lines), match_line + 10)
            snippet = "\n".join(lines[start:end])
            end_line = start if end <= start else end - 1

            grep_chunks.append(
                {
                    "file_path": rel_path,
                    "start_line": start,
                    "end_line": end_line,
                    "text": snippet,
                    "similarity": None,
                    "source": "grep",
                }
            )

    return grep_chunks
