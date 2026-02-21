import os
import uuid
import zipfile
import shutil
from pathlib import Path
from typing import Tuple

# ── Constants ──────────────────────────────────────────────────────────────────
MAX_COMPRESSED_BYTES   = 15 * 1024 * 1024   # 15 MB
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MB

ALLOWED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx"}

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", "__pycache__",
    ".venv", "venv", "env", ".mypy_cache", ".pytest_cache",
    "coverage", ".next", "out", ".cache",
}

REPOS_ROOT = Path("./repos")


# ── Exceptions ─────────────────────────────────────────────────────────────────
class ValidationError(Exception):
    pass


# ── Public entry point ─────────────────────────────────────────────────────────
def validate_and_extract(zip_bytes: bytes) -> Tuple[str, Path]:
    _check_compressed_size(zip_bytes)
    _check_is_zip(zip_bytes)

    repo_id   = _new_repo_id()
    repo_path = REPOS_ROOT / repo_id
    repo_path.mkdir(parents=True, exist_ok=True)

    tmp_dir = repo_path / "_tmp_extract"
    try:
        tmp_dir.mkdir()
        _extract_zip(zip_bytes, tmp_dir)
        _check_uncompressed_size(tmp_dir)
        kept = _copy_allowed_files(tmp_dir, repo_path)
        if kept == 0:
            raise ValidationError(
                "No supported source files found in the ZIP. "
                f"Supported extensions: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
    finally:
        if tmp_dir.exists():
            shutil.rmtree(tmp_dir)

    return repo_id, repo_path


# ── Validators ─────────────────────────────────────────────────────────────────
def _check_compressed_size(zip_bytes: bytes) -> None:
    size = len(zip_bytes)
    if size > MAX_COMPRESSED_BYTES:
        mb = size / (1024 * 1024)
        raise ValidationError(
            f"ZIP file is {mb:.1f} MB — exceeds the {MAX_COMPRESSED_BYTES // (1024*1024)} MB limit."
        )

def _check_is_zip(zip_bytes: bytes) -> None:
    import io
    if not zipfile.is_zipfile(io.BytesIO(zip_bytes)):
        raise ValidationError("Uploaded file is not a valid ZIP archive.")

def _extract_zip(zip_bytes: bytes, dest: Path) -> None:
    import io
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        _check_zip_safety(zf, dest)
        zf.extractall(dest)

def _check_zip_safety(zf: zipfile.ZipFile, dest: Path) -> None:
    dest_resolved = dest.resolve()
    for member in zf.namelist():
        member_path = (dest / member).resolve()
        if not str(member_path).startswith(str(dest_resolved)):
            raise ValidationError(
                f"ZIP contains unsafe path: '{member}'. Upload rejected."
            )

def _check_uncompressed_size(extracted_dir: Path) -> None:
    total = sum(
        f.stat().st_size
        for f in extracted_dir.rglob("*")
        if f.is_file()
    )
    if total > MAX_UNCOMPRESSED_BYTES:
        mb = total / (1024 * 1024)
        raise ValidationError(
            f"Uncompressed repo is {mb:.1f} MB — exceeds the "
            f"{MAX_UNCOMPRESSED_BYTES // (1024*1024)} MB limit."
        )

def _copy_allowed_files(src: Path, dest: Path) -> int:
    kept = 0
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext not in ALLOWED_EXTENSIONS:
                continue
            src_file  = Path(root) / filename
            rel_path  = src_file.relative_to(src)
            dest_file = dest / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            kept += 1
    return kept

def _new_repo_id() -> str:
    return uuid.uuid4().hex[:12]