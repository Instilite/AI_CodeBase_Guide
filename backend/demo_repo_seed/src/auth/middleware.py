import hashlib


def verify_credentials(username: str, password: str) -> bool:
    """Validate user credentials against an in-memory store."""
    users = {
        "admin": hashlib.sha256("secret".encode()).hexdigest(),
        "guest": hashlib.sha256("guest".encode()).hexdigest(),
    }
    digest = hashlib.sha256(password.encode()).hexdigest()
    return users.get(username) == digest


def issue_token(username: str) -> str:
    return f"token::{username}"
