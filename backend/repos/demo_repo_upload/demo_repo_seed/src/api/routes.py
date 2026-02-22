from src.auth.middleware import verify_credentials, issue_token


def login(username: str, password: str) -> dict:
    ok = verify_credentials(username, password)
    if not ok:
        return {"ok": False, "token": None}
    return {"ok": True, "token": issue_token(username)}


def refresh(username: str) -> dict:
    return {"ok": True, "token": issue_token(username)}
