from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import time
from urllib.parse import quote


def generate_totp_secret(length: int = 20) -> str:
    return base64.b32encode(os.urandom(length)).decode("utf-8").rstrip("=")


def build_otpauth_uri(*, secret: str, account_name: str, issuer: str) -> str:
    label = quote(f"{issuer}:{account_name}")
    encoded_issuer = quote(issuer)
    return f"otpauth://totp/{label}?secret={secret}&issuer={encoded_issuer}&algorithm=SHA1&digits=6&period=30"


def _normalize_secret(secret: str) -> bytes:
    compact = str(secret or "").strip().replace(" ", "").upper()
    padding = "=" * (-len(compact) % 8)
    return base64.b32decode(compact + padding, casefold=True)


def _hotp(secret: str, counter: int, digits: int = 6) -> str:
    key = _normalize_secret(secret)
    message = counter.to_bytes(8, "big")
    digest = hmac.new(key, message, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = int.from_bytes(digest[offset:offset + 4], "big") & 0x7FFFFFFF
    return str(binary % (10 ** digits)).zfill(digits)


def verify_totp_code(secret: str, code: str, *, window: int = 1, period: int = 30, at_time: int | None = None) -> bool:
    normalized_code = "".join(ch for ch in str(code or "") if ch.isdigit())
    if len(normalized_code) != 6:
        return False
    now = at_time or int(time.time())
    counter = now // period
    for offset in range(-window, window + 1):
        if hmac.compare_digest(_hotp(secret, counter + offset), normalized_code):
            return True
    return False


def generate_recovery_codes(count: int = 8) -> list[str]:
    codes: list[str] = []
    for _ in range(count):
        left = secrets.token_hex(2).upper()
        right = secrets.token_hex(2).upper()
        codes.append(f"{left}-{right}")
    return codes


def hash_recovery_code(code: str) -> str:
    normalized = str(code or "").strip().replace(" ", "").replace("-", "").upper()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
