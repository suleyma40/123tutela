from __future__ import annotations

from typing import Any

from backend.document_rules import get_document_rule


def _normalize(value: str | None) -> str:
    return str(value or "").lower().strip()


def evaluate_document_rule(
    *,
    recommended_action: str | None,
    workflow_type: str | None,
    description: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    rule = get_document_rule(recommended_action, workflow_type)
    intake = facts.get("intake_form") or {}
    full_text = _normalize(
        " ".join(
            [
                str(description or ""),
                str(facts.get("hechos_principales") or ""),
                str(intake.get("case_story") or ""),
                str(intake.get("concrete_request") or ""),
                str(intake.get("key_dates") or ""),
                str(intake.get("target_entity") or ""),
                str(intake.get("eps_name") or ""),
                str(intake.get("diagnosis") or ""),
                str(intake.get("treatment_needed") or ""),
                str(intake.get("urgency_detail") or ""),
                str(intake.get("tutela_previous_action_detail") or ""),
                str(intake.get("tutela_oath_statement") or ""),
                str(intake.get("tutela_no_temperity_detail") or ""),
                str(intake.get("tutela_other_means_detail") or ""),
                str(intake.get("tutela_immediacy_detail") or ""),
            ]
        )
    )
    blocking_issues: list[str] = []
    warnings: list[str] = []

    if not facts.get("entidades_involucradas") and not str(intake.get("target_entity") or intake.get("eps_name") or "").strip():
        blocking_issues.append("Falta identificar claramente el destinatario o sujeto pasivo del documento.")
    if len(str(facts.get("hechos_principales") or "").strip()) < 80 and len(str(intake.get("case_story") or "").strip()) < 80:
        blocking_issues.append("Los hechos consolidados siguen siendo breves para sostener un documento serio.")
    if "pretension concreta" in rule["required_elements"] and not (
        str(intake.get("concrete_request") or "").strip()
        or any(word in full_text for word in ["solicito", "pido", "requiero", "pretendo", "ordenen", "corrijan"])
    ):
        blocking_issues.append("El documento requiere una pretension concreta mejor formulada.")

    action_key = rule["action_key"]
    if action_key == "accion de tutela":
        if not (
            str(intake.get("tutela_oath_statement") or "").strip()
            or str(intake.get("tutela_no_temperity_detail") or "").strip()
            or any(word in full_text for word in ["no temeridad", "no he presentado otra tutela", "otra tutela", "juramento"])
        ):
            blocking_issues.append("La tutela debe incluir una declaracion de no temeridad o explicar si existio tutela previa.")
        if not (
            str(intake.get("tutela_other_means_detail") or "").strip()
            or any(word in full_text for word in ["otro medio", "subsidiariedad", "perjuicio irremediable", "no existe otro medio eficaz"])
        ):
            blocking_issues.append("La tutela debe justificar subsidiariedad o perjuicio irremediable.")
        if not (
            str(intake.get("tutela_immediacy_detail") or "").strip()
            or any(word in full_text for word in ["inmediatez", "reciente", "actualmente", "hoy", "sigue ocurriendo"])
        ):
            blocking_issues.append("La tutela debe explicar por que la vulneracion es actual o por que se cumple la inmediatez.")
        if not any(word in full_text for word in ["urgencia", "riesgo", "perjuicio", "vulneracion", "derecho fundamental"]):
            blocking_issues.append("La tutela necesita dejar mejor descritos los hechos actuales del paciente, la barrera de la EPS y el riesgo que sigue ocurriendo hoy.")
        if any(word in full_text for word in ["particular", "empresa privada", "privada", "privado"]) and not any(
            word in full_text for word in ["servicio publico", "indefension", "subordinacion", "posicion dominante", "articulo 42", "art. 42"]
        ):
            warnings.append("Si la tutela va contra un particular, la IA debe justificar internamente la procedencia con base en el articulo 42 del Decreto 2591 de 1991.")
    elif action_key == "derecho de peticion":
        if not any(word in full_text for word in ["15 dias", "10 dias", "30 dias", "ley 1755"]):
            warnings.append("Conviene incorporar el termino legal de respuesta o la referencia expresa a la Ley 1755 de 2015.")
        if "privada" in full_text and not any(word in full_text for word in ["servicio publico", "interes colectivo", "posicion dominante"]):
            blocking_issues.append("Si el derecho de peticion va contra un privado, debe explicarse por que ese particular esta obligado a responder.")
        if not (
            str(intake.get("numbered_requests") or "").strip()
            or any(word in full_text for word in ["1)", "1.", "solicitudes numeradas", "respondan", "informen", "entreguen", "certifiquen"])
        ):
            warnings.append("Conviene reforzar las solicitudes numeradas para que el derecho de peticion sea mas claro.")
    elif action_key == "accion de cumplimiento":
        if not any(word in full_text for word in ["ley", "decreto", "resolucion", "acto administrativo"]):
            blocking_issues.append("La accion de cumplimiento exige identificar la norma o el acto incumplido.")

    return {
        "rule": rule,
        "status": "requires_more_data" if blocking_issues else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }
