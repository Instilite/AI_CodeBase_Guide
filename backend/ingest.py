from __future__ import annotations

import hashlib
import io
import re
import shutil
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Optional, Tuple

COMPRESSED_LIMIT_BYTES = 15 * 1024 * 1024  # 15 MB
UNCOMPRESSED_LIMIT_BYTES = 200 * 1024 * 1024  # 200 MB

ALLOWED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".css",
    ".html",
    ".md",
    ".go",
    ".java",
    ".rb",
    ".rs",
    ".cpp",
    ".c",
    ".h",
}

SKIP_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "__pycache__",
    ".venv",
    "venv",
}

_DRIVE_PREFIX_RE = re.compile(r"^[A-Za-z]:")
_KEEP_CHARS_RE = re.compile(r"[^a-z0-9_-]+")


class ZipValidationError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        error_code: str,
        message: str,
        details: Optional[Dict[str, object]] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message
        self.details = details


def parse_content_length(content_length: Optional[str]) -> Optional[int]:
    if not content_length:
        return None
    try:
        return int(content_length)
    except ValueError:
        return None


def sanitize_repo_id(filename: str, repos_root: Path) -> str:
    base = Path(filename).stem.lower().replace(" ", "_")
    base = _KEEP_CHARS_RE.sub("", base).strip("_")
    if not base:
        base = "repo"
    base = base[:48]

    candidate = base
    if (repos_root / candidate).exists():
        stamp = f"{filename}:{time.time_ns()}"
        suffix = hashlib.sha1(stamp.encode("utf-8", errors="ignore")).hexdigest()[:8]
        candidate = f"{base[:39]}_{suffix}" if len(base) > 39 else f"{base}_{suffix}"

    return candidate


def enforce_compressed_limit(content_length_header: Optional[int], actual_bytes: int) -> None:
    if content_length_header is not None and content_length_header > COMPRESSED_LIMIT_BYTES:
        raise ZipValidationError(
            status_code=413,
            error_code="zip_too_large",
            message="Compressed upload size exceeds the 15 MB limit.",
            details={"limit_bytes": COMPRESSED_LIMIT_BYTES, "received_bytes": content_length_header},
        )

    if actual_bytes > COMPRESSED_LIMIT_BYTES:
        raise ZipValidationError(
            status_code=413,
            error_code="zip_too_large",
            message="Compressed upload size exceeds the 15 MB limit.",
            details={"limit_bytes": COMPRESSED_LIMIT_BYTES, "received_bytes": actual_bytes},
        )


def validate_and_extract_zip(zip_bytes: bytes, tmp_dir: Path) -> Tuple[int, int]:
    """
    Validate and extract according to the contract.
    Returns (declared_total_bytes, on_disk_total_bytes).
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), mode="r") as zf:
            infos = zf.infolist()
            declared_total = sum(info.file_size for info in infos)
            if declared_total > UNCOMPRESSED_LIMIT_BYTES:
                raise ZipValidationError(
                    status_code=413,
                    error_code="zip_too_large",
                    message="Uncompressed content size exceeds the 200 MB limit.",
                    details={"limit_bytes": UNCOMPRESSED_LIMIT_BYTES, "declared_bytes": declared_total},
                )

            validate_zip_entries(infos, tmp_dir)

            tmp_dir.mkdir(parents=True, exist_ok=True)
            zf.extractall(path=tmp_dir)

            on_disk_total = compute_directory_size(tmp_dir)
            if on_disk_total > UNCOMPRESSED_LIMIT_BYTES:
                raise ZipValidationError(
                    status_code=413,
                    error_code="zip_too_large",
                    message="Uncompressed content size exceeds the 200 MB limit.",
                    details={"limit_bytes": UNCOMPRESSED_LIMIT_BYTES, "declared_bytes": on_disk_total},
                )

            return declared_total, on_disk_total

    except zipfile.BadZipFile as exc:
        raise ZipValidationError(
            status_code=422,
            error_code="zip_invalid",
            message="Uploaded file is not a valid ZIP archive.",
            details=None,
        ) from exc


def validate_zip_entries(entries: Iterable[zipfile.ZipInfo], extraction_root: Path) -> None:
    root_resolved = extraction_root.resolve()

    for info in entries:
        name = info.filename
        normalized = name.replace("\\", "/")
        parts = PurePosixPath(normalized).parts

        if normalized.startswith(("/", "\\")) or PurePosixPath(normalized).is_absolute() or _DRIVE_PREFIX_RE.match(normalized):
            raise ZipValidationError(
                status_code=422,
                error_code="zip_invalid",
                message="Zip-slip path traversal detected. Upload rejected.",
                details={"offending_entry": name},
            )

        if ".." in parts:
            raise ZipValidationError(
                status_code=422,
                error_code="zip_invalid",
                message="Zip-slip path traversal detected. Upload rejected.",
                details={"offending_entry": name},
            )

        candidate = (extraction_root / normalized).resolve()
        if not candidate.is_relative_to(root_resolved):
            raise ZipValidationError(
                status_code=422,
                error_code="zip_invalid",
                message="Zip-slip path traversal detected. Upload rejected.",
                details={"offending_entry": name},
            )


def compute_directory_size(root: Path) -> int:
    total = 0
    for file_path in root.rglob("*"):
        if file_path.is_file():
            total += file_path.stat().st_size
    return total


def is_binary_file(path: Path) -> bool:
    with path.open("rb") as fh:
        head = fh.read(8192)
    return b"\x00" in head


def should_skip_path(relative_path: Path) -> bool:
    parts_lower = {part.lower() for part in relative_path.parts}
    return any(skip_dir in parts_lower for skip_dir in SKIP_DIRS)


def should_keep_file(relative_path: Path, absolute_path: Path) -> bool:
    if should_skip_path(relative_path):
        return False
    if absolute_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return False
    if is_binary_file(absolute_path):
        return False
    return True


def move_filtered_files(extracted_root: Path, repo_root: Path) -> List[str]:
    repo_root.mkdir(parents=True, exist_ok=True)
    kept_files: List[str] = []

    for file_path in sorted(extracted_root.rglob("*")):
        if not file_path.is_file():
            continue

        rel_path = file_path.relative_to(extracted_root)
        if not should_keep_file(rel_path, file_path):
            continue

        destination = repo_root / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(destination))
        kept_files.append(rel_path.as_posix())

    return kept_files


def copy_filtered_files(source_root: Path, repo_root: Path) -> List[str]:
    repo_root.mkdir(parents=True, exist_ok=True)
    kept_files: List[str] = []

    for file_path in sorted(source_root.rglob("*")):
        if not file_path.is_file():
            continue

        rel_path = file_path.relative_to(source_root)
        if not should_keep_file(rel_path, file_path):
            continue

        destination = repo_root / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, destination)
        kept_files.append(rel_path.as_posix())

    return kept_files


def cleanup_path(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        try:
            path.unlink(missing_ok=True)
        except TypeError:
            if path.exists():
                path.unlink()
