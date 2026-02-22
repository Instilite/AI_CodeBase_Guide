from src.auth.middleware import verify_credentials


def test_verify_credentials_admin() -> None:
    assert verify_credentials("admin", "secret") is True


def test_verify_credentials_invalid() -> None:
    assert verify_credentials("admin", "wrong") is False
