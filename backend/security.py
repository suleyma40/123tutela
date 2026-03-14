from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time


PBKDF2_ROUNDS = 390000


def _b64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("utf-8").rstrip("=")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)
    return f"{_b64url_encode(salt)}${_b64url_encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_b64, digest_b64 = password_hash.split("$", 1)
    except ValueError:
        return False

    expected = _b64url_decode(digest_b64)
    computed = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), _b64url_decode(salt_b64), PBKDF2_ROUNDS
    )
    return hmac.compare_digest(computed, expected)


def create_token(subject: str, email: str, secret: str, ttl_hours: int = 168) -> str:
    payload = {
        "sub": subject,
        "email": email,
        "exp": int(time.time()) + ttl_hours * 3600,
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return f"{body}.{_b64url_encode(signature)}"


def decode_token(token: str, secret: str) -> dict[str, str | int]:
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("Token mal formado.") from exc

    expected = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64url_decode(signature), expected):
        raise ValueError("Token inválido.")

    payload = json.loads(_b64url_decode(body).decode("utf-8"))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expirado.")
    return payload
