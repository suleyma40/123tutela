from __future__ import annotations

import json
from typing import Any
from urllib import error, request

from backend.config import settings


def score_document_with_claude(
    *,
    case: dict[str, Any],
    document: str,
    base_review: dict[str, Any],
) -> dict[str, Any] | None:
    if not settings.anthropic_api_key:
        return None

    prompt = {
        "case_summary": {
            "category": case.get("categoria") or case.get("category"),
            "workflow_type": case.get("workflow_type"),
            "recommended_action": case.get("recommended_action"),
            "rights": (case.get("legal_analysis") or {}).get("derechos_vulnerados") or [],
            "verified_sources": ((case.get("facts") or {}).get("source_validation_policy") or {}).get("verified_sources") or [],
            "agent_state": ((case.get("facts") or {}).get("agent_state") or {}),
        },
        "base_review": base_review,
        "document": document,
        "instructions": [
            "Evalua el borrador juridico con criterio estricto y conservador.",
            "No exijas al usuario tareas tecnicas o juridicas que le correspondan al sistema.",
            "Bloquea solo si el documento es riesgoso, inventa soporte o omite elementos esenciales.",
            "Si faltan citas verificadas, indica que el sistema debe reforzarlas internamente.",
            "Si el documento ya es radicable y solo tiene mejoras menores de estilo, no reduzcas severamente el puntaje.",
            "Si es un caso de salud, valora con prioridad diagnostico, servicio requerido, barrera de EPS/IPS y riesgo actual del paciente.",
            "Responde solo JSON con: adjusted_score, blocking_issues, warnings, strengths, improvements, verdict.",
        ],
    }

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 900,
        "temperature": 0,
        "system": "Eres un revisor juridico extremadamente estricto. Evalua calidad de documentos legales colombianos.",
        "messages": [
            {
                "role": "user",
                "content": json.dumps(prompt, ensure_ascii=False),
            }
        ],
    }
    raw_request = request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(raw_request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return None

    content = body.get("content") or []
    text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
    if not text_parts:
        return None

    try:
        parsed = json.loads("".join(text_parts))
    except json.JSONDecodeError:
        return None

    return {
        "model": settings.anthropic_model,
        "adjusted_score": parsed.get("adjusted_score"),
        "blocking_issues": parsed.get("blocking_issues") or [],
        "warnings": parsed.get("warnings") or [],
        "strengths": parsed.get("strengths") or [],
        "improvements": parsed.get("improvements") or [],
        "verdict": parsed.get("verdict") or "reviewed",
    }
