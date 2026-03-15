from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import UTC, datetime
from typing import Any

from backend.config import settings


def ensure_checkout_configured() -> None:
    missing = [
        key
        for key, value in {
            "WOMPI_PUBLIC_KEY": settings.wompi_public_key,
            "WOMPI_INTEGRITY_SECRET": settings.wompi_integrity_secret,
            "WOMPI_PAYMENT_REDIRECT_URL": settings.wompi_payment_redirect_url,
        }.items()
        if not value
    ]
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Configuración incompleta de Wompi: {joined}")


def ensure_webhook_configured() -> None:
    if not settings.wompi_event_secret:
        raise RuntimeError("Configuración incompleta de Wompi: WOMPI_EVENT_SECRET")


def build_reference(case_id: str, product_code: str) -> str:
    suffix = uuid.uuid4().hex[:10]
    compact_case = case_id.replace("-", "")[:8]
    return f"123T-{product_code.upper()}-{compact_case}-{suffix}".upper()


def amount_cop_to_cents(amount_cop: int) -> int:
    return amount_cop * 100


def build_integrity_signature(reference: str, amount_in_cents: int, currency: str) -> str:
    raw = f"{reference}{amount_in_cents}{currency}{settings.wompi_integrity_secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_event_environment(sandbox: bool) -> str:
    return "sandbox" if sandbox else "production"


def get_nested_value(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for segment in path.split("."):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
        else:
            return None
    return current


def compute_event_checksum(event_payload: dict[str, Any], event_secret: str) -> str:
    data = event_payload.get("data") or {}
    signature = event_payload.get("signature") or {}
    properties = signature.get("properties") or []
    values = []
    for prop in properties:
        values.append("" if (value := get_nested_value(data, prop)) is None else str(value))
    values.append(signature.get("timestamp", ""))
    values.append(event_secret)
    raw = "".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_event_signature(event_payload: dict[str, Any], event_secret: str) -> bool:
    signature = event_payload.get("signature") or {}
    provided = signature.get("checksum")
    if not provided:
        return False
    expected = compute_event_checksum(event_payload, event_secret)
    return hmac.compare_digest(provided, expected)


def extract_transaction_from_event(event_payload: dict[str, Any]) -> dict[str, Any]:
    data = event_payload.get("data") or {}
    if isinstance(data.get("transaction"), dict):
        return data["transaction"]
    return data


def parse_approved_at(transaction: dict[str, Any]) -> datetime | None:
    value = transaction.get("finalized_at") or transaction.get("created_at")
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return None


def build_checkout_payload(
    *,
    reference: str,
    amount_in_cents: int,
    product_name: str,
    description: str,
    customer_email: str,
) -> dict[str, Any]:
    ensure_checkout_configured()
    return {
        "widget_url": settings.wompi_widget_url,
        "public_key": settings.wompi_public_key,
        "currency": "COP",
        "amount_in_cents": amount_in_cents,
        "reference": reference,
        "signature:integrity": build_integrity_signature(reference, amount_in_cents, "COP"),
        "redirect-url": settings.wompi_payment_redirect_url,
        "customer-data:email": customer_email,
        "name": product_name,
        "description": description,
    }
