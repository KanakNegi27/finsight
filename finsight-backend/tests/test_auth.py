import pytest

import database
from services import auth


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setenv("FINSIGHT_DB_PATH", str(tmp_path / "test.db"))
    database.init_db()
    yield


def test_register_then_login():
    user = auth.register_user("Ada", "ada@example.com", "supersecret")

    assert user["email"] == "ada@example.com"

    authenticated = auth.authenticate_user("ada@example.com", "supersecret")
    assert authenticated["id"] == user["id"]


def test_duplicate_email_rejected():
    auth.register_user("Ada", "ada@example.com", "supersecret")

    with pytest.raises(auth.AuthError):
        auth.register_user("Ada2", "ada@example.com", "anotherpass")


def test_wrong_password_rejected():
    auth.register_user("Ada", "ada@example.com", "supersecret")

    with pytest.raises(auth.AuthError):
        auth.authenticate_user("ada@example.com", "wrongpass")


def test_password_is_hashed_not_stored_plain():
    auth.register_user("Ada", "ada@example.com", "supersecret")
    stored = database.get_user_by_email("ada@example.com")

    assert stored["password_hash"] != "supersecret"
    assert len(stored["password_hash"]) == 64


def test_token_roundtrip_and_tampering():
    user = auth.register_user("Ada", "ada@example.com", "supersecret")
    token = auth.create_token(user["id"])

    assert auth.verify_token(token) == user["id"]

    with pytest.raises(auth.AuthError):
        auth.verify_token(token + "tampered")
