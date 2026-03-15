from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _validate_tutela(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    dates = facts.get("fechas_mencionadas") or []
    problem = _lower(facts.get("problema_central"))
    text = _lower(description)

    if not entities:
      problems.append("Falta identificar con claridad la entidad o persona accionada.")
    if not dates:
      problems.append("Faltan fechas o referencias temporales mínimas para construir la cronología.")
    if len(_text(facts.get("hechos_principales"))) < 80:
      problems.append("Los hechos extraídos son demasiado breves para sustentar una tutela sólida.")
    if not _has_any(text, ["derecho", "salud", "vida", "mínimo vital", "minimo vital", "petición", "peticion", "urgencia", "riesgo", "afecta", "vulner"]):
      warnings.append("No aparece claramente explicado el derecho afectado o el riesgo actual.")
    if not _has_any(text, ["solicito", "pido", "requiero", "necesito", "pretendo", "ordenen"]):
      warnings.append("No se ve una pretensión concreta en el relato del usuario.")
    if not prior_actions and not _has_any(text, ["urgencia", "riesgo", "inmediato", "grave", "menor", "embarazada", "discapacidad"]):
      warnings.append("Puede faltar justificación de vía previa o de urgencia para soportar la procedencia de la tutela.")
    if "salud" in problem and not _has_any(text, ["eps", "ips", "orden médica", "orden medica", "tratamiento", "cita", "medicamento"]):
      warnings.append("En salud conviene pedir datos de EPS, orden médica o tratamiento para evitar una tutela débil.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_derecho_peticion(description: str, facts: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar la entidad o destinatario del derecho de petición.")
    if not _has_any(text, ["solicito", "pido", "requiero", "entreguen", "respondan", "informen", "certifiquen"]):
        problems.append("No está claro qué se solicita exactamente en el derecho de petición.")
    if len(_text(facts.get("hechos_principales"))) < 60:
        warnings.append("Los hechos del derecho de petición todavía son escasos para soportar una respuesta de fondo.")
    if not _has_any(text, ["respuesta", "información", "informacion", "documento", "copia", "consulta"]):
        warnings.append("Conviene precisar mejor el tipo de petición para ajustar el término legal de respuesta.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_habeas_data(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar la entidad o base de datos que trata la información.")
    if not _has_any(text, ["dato", "reporte", "historial", "datacredito", "cifin", "información", "informacion"]):
        problems.append("No se identifica con claridad cuál es el dato o reporte cuestionado.")
    if not _has_any(text, ["corregir", "actualizar", "eliminar", "suprimir", "rectificar"]):
        problems.append("Debe quedar claro si se pide corregir, actualizar o suprimir el dato.")
    if not prior_actions:
        warnings.append("Conviene validar si ya hubo reclamación previa ante la fuente o responsable del tratamiento.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def validate_intake(
    *,
    category: str,
    workflow_type: str,
    recommended_action: str,
    description: str,
    facts: dict[str, Any],
    prior_actions: list[str],
) -> dict[str, Any]:
    action = _lower(recommended_action)
    category_lower = _lower(category)

    if "tutela" in action or workflow_type == "tutela":
        return _validate_tutela(description, facts, prior_actions)
    if "peticion" in action:
        return _validate_derecho_peticion(description, facts)
    if "habeas" in action or category_lower == "datos":
        return _validate_habeas_data(description, facts, prior_actions)

    return {"status": "not_scored", "blocking_issues": [], "warnings": []}
