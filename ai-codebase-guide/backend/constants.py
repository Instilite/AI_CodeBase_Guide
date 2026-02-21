from pathlib import Path

OVERVIEW_KEYWORDS = [
    "overview",
    "architecture",
    "structure",
    "entry point",
    "entrypoint",
    "flow",
    "project map",
    "how does this repo work",
    "how does this project work",
    "main files",
    "important files",
    "explain the repo",
    "explain the project",
]

allowed_extensions = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rb", ".rs"}
excluded_dirnames = {
    "test",
    "tests",
    "spec",
    "specs",
    "__tests__",
    "mocks",
    "fixtures",
}

repo_root = "./repos"

# Uppercase aliases for internal use.
ALLOWED_EXTENSIONS = allowed_extensions
EXCLUDED_DIRNAMES = excluded_dirnames
REPO_ROOT = repo_root


def get_collection_name(repo_id: str) -> str:
    return f"repo_{repo_id}"


def get_repo_root_path() -> Path:
    return Path(repo_root).resolve()
