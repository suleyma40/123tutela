from __future__ import annotations

from typing import Any

from backend import repository_ext as repository
from backend.entity_catalog import normalize_entity_text, search_enriched_entities
from backend.entity_excel_catalog import search_excel_entities


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(cleaned)
    return ordered


def _infer_type_from_row(row: dict[str, Any]) -> str | None:
    text = " ".join(
        str(row.get(key) or "")
        for key in ("modulo", "paso_flujo", "observaciones", "nombre_entidad")
    ).lower()
    if any(token in text for token in ("eps", "salud", "supersalud")):
        return "eps"
    if any(token in text for token in ("banco", "financ", "superfinanc")):
        return "banco"
    if any(token in text for token in ("telecom", "internet", "movil", "claro", "tigo", "wom")):
        return "telecom"
    if any(token in text for token in ("servicios", "energia", "agua", "gas", "superservicios")):
        return "servicio_publico"
    if any(token in text for token in ("entidades públicas", "entidades publicas", "ministerio", "alcaldia", "superintendencia")):
        return "gobierno"
    return None


def _build_routing_channel(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "channel": row.get("canal_envio"),
        "contact": row.get("contacto_envio"),
        "automatable": bool(row.get("automatizable")),
        "genera_radicado": bool(row.get("genera_radicado")),
        "response_window": row.get("plazo_respuesta"),
        "notes": row.get("observaciones"),
    }


def _merge_operational_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    for row in rows:
        name = str(row.get("nombre_entidad") or "").strip()
        if not name:
            continue
        key = normalize_entity_text(name)
        current = grouped.setdefault(
            key,
            {
                "name": name,
                "type": _infer_type_from_row(row),
                "source": "operativa",
                "routing_channels": [],
                "pqrs_emails": [],
                "notification_emails": [],
                "phones": [],
            },
        )

        channel = _build_routing_channel(row)
        if channel["contact"]:
            contact = str(channel["contact"])
            if "@" in contact:
                current["pqrs_emails"].append(contact)
            elif contact.startswith("http"):
                current["website"] = contact
            else:
                current["phones"].append(contact)
        current["routing_channels"].append(channel)

    for current in grouped.values():
        current["pqrs_emails"] = _dedupe_strings(current["pqrs_emails"])
        current["notification_emails"] = _dedupe_strings(current["notification_emails"])
        current["phones"] = _dedupe_strings(current["phones"])

    return list(grouped.values())


def _merge_catalog_sources(*sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}

    for source in sources:
        for item in source:
            key = normalize_entity_text(item["name"])
            current = merged.get(key, {"routing_channels": [], "pqrs_emails": [], "notification_emails": [], "phones": []})
            merged[key] = {
                **current,
                **{k: v for k, v in item.items() if k not in {"aliases_search", "name_search"}},
                "routing_channels": [*(current.get("routing_channels") or []), *(item.get("routing_channels") or [])],
                "pqrs_emails": _dedupe_strings([*(current.get("pqrs_emails") or []), *(item.get("pqrs_emails") or [])]),
                "notification_emails": _dedupe_strings([*(current.get("notification_emails") or []), *(item.get("notification_emails") or [])]),
                "phones": _dedupe_strings([*(current.get("phones") or []), *(item.get("phones") or [])]),
            }

    results = list(merged.values())
    source_priority = {"precargada": 0, "excel_maestro": 1, "operativa": 2}
    results.sort(key=lambda item: (source_priority.get(item.get("source"), 9), item["name"]))
    return results


def search_entity_directory(query: str, limit: int = 8) -> list[dict[str, Any]]:
    if len((query or "").strip()) < 2:
        return []

    enriched = search_enriched_entities(query, limit=limit)
    excel_catalog = search_excel_entities(query, limit=max(limit * 2, 12))
    operational_rows = repository.search_entity_directory(query, limit=max(limit * 3, 12))
    operational = _merge_operational_rows(operational_rows)
    merged = _merge_catalog_sources(operational, excel_catalog, enriched)
    return merged[:limit]
