"""Authentication helpers.

Implements password hashing (PBKDF2-HMAC-SHA256) and stateless bearer
tokens signed with HMAC-SHA256 using only the standard library. This
keeps the project dependency-free while still avoiding plain-text
passwords and unsigned tokens.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

import database

SECRET_KEY = os.environ.get(
    "FINSIGHT_SECRET_KEY",
    "finsight-dev-secret-change-me",
).encode()

TOKEN_TTL_SECONDS = int(os.environ.get("FINSIGHT_TOKEN_TTL", 60 * 60 * 24 * 7))
PBKDF2_ITERATIONS = 120_000


class AuthError(Exception):
    """Raised when authentication fails."""


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    candidate = hash_password(password, salt)
    return hmac.compare_digest(candidate, expected_hash)


def _sign(payload: bytes) -> str:
    signature = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()
    return _b64encode(signature)


def create_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    encoded = _b64encode(json.dumps(payload).encode())
    return f"{encoded}.{_sign(encoded.encode())}"


def verify_token(token: str) -> int:
    """Return the user id if the token is valid, otherwise raise AuthError."""

    try:
        encoded, signature = token.split(".", 1)
    except ValueError as exc:
        raise AuthError("Malformed token.") from exc

    if not hmac.compare_digest(_sign(encoded.encode()), signature):
        raise AuthError("Invalid token signature.")

    try:
        payload = json.loads(_b64decode(encoded))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthError("Malformed token payload.") from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise AuthError("Token has expired.")

    return int(payload["sub"])


def register_user(name: str, email: str, password: str) -> dict:
    if database.get_user_by_email(email):
        raise AuthError("An account with this email already exists.")

    salt = secrets.token_hex(16)
    password_hash = hash_password(password, salt)
    return database.create_user(name, email, password_hash, salt)


def authenticate_user(email: str, password: str) -> dict:
    user = database.get_user_by_email(email)

    if not user or not verify_password(
        password,
        user["salt"],
        user["password_hash"],
    ):
        raise AuthError("Incorrect email or password.")

    return user


def public_user(user: dict) -> dict:
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
    }
