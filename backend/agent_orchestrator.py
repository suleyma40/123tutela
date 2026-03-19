from __future__ import annotations

import re
from typing import Any

from backend.agent_registry import list_health_block_documents, resolve_health_document


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _join_texts(*parts: Any) -> str:
    return " ".join(_text(part) for part in parts if _text(part))


def _build_next_prompt(*, intake: dict[str, Any], facts: dict[str, Any], workflow_type: str) -> dict[str, Any] | None:
    acting_capacity = _lower(intake.get("acting_capacity"))
    if acting_capacity and acting_capacity != "nombre_propio" and not _text(intake.get("represented_person_name")):
        return {
            "id": "represented_person_name",
            "question": "Como se llama el paciente o la persona afectada por quien presentas este caso?",
            "placeholder": "Ej: Jeronimo Perez",
            "multiline": False,
            "why": "Necesitamos identificar claramente a la persona protegida en el documento.",
        }
    if acting_capacity and acting_capacity != "nombre_propio" and not _text(intake.get("represented_person_age")):
        return {
            "id": "represented_person_age",
            "question": "Que edad tiene el paciente o la persona afectada?",
            "placeholder": "Ej: 8 anos",
            "multiline": False,
            "why": "La edad ayuda a sustentar proteccion especial y urgencia medica.",
        }
    if not (_text(intake.get("target_entity")) or _text(intake.get("eps_name"))):
        return {
            "id": "target_entity",
            "question": "Cual EPS o IPS es la responsable del problema en salud?",
            "placeholder": "Ej: Nueva EPS, Sura EPS, IPS X",
            "multiline": False,
            "why": "Sin entidad accionada no se puede cerrar el documento.",
        }
    if not _text(intake.get("diagnosis")):
        return {
            "id": "diagnosis",
            "question": "Cual es el diagnostico o la condicion de salud principal del paciente?",
            "placeholder": "Ej: anemia de celulas falciformes",
            "multiline": False,
            "why": "El documento debe identificar el problema medico central.",
        }
    if not _text(intake.get("treatment_needed")):
        return {
            "id": "treatment_needed",
            "question": "Que medicamento, examen, terapia, procedimiento o servicio fue ordenado?",
            "placeholder": "Ej: hidroxiurea 500 mg cada 8 horas por 6 meses",
            "multiline": False,
            "why": "El juez o la EPS deben saber que servicio concreto se esta pidiendo.",
        }
    if not (
        _text(intake.get("medical_order_date"))
        or _text(intake.get("treating_doctor_name"))
        or (facts.get("uploaded_evidence_files") or [])
    ):
        return {
            "id": "medical_support",
            "question": "Sube la orden medica, formula o historia clinica, o cuentame la fecha de la orden y el nombre del medico tratante.",
            "placeholder": "Ej: la orden fue el 4 de marzo y la hizo la Dra. X",
            "multiline": True,
            "why": "Hace falta un soporte medico minimo para cerrar bien el caso de salud.",
        }
    if workflow_type == "tutela" and not (
        _text(intake.get("eps_request_date"))
        or _text(intake.get("eps_response_detail"))
        or _lower(intake.get("prior_claim")) in {"si", "sí", "no", "aun no", "aún no", "no_aun_no"}
    ):
        return {
            "id": "eps_barrier",
            "question": "Que hizo la EPS despues de pedir el servicio: nego, guardo silencio, demoro, no agendo o puso otra barrera?",
            "placeholder": "Ej: se pidio por WhatsApp y no respondieron, o negaron por no PBS",
            "multiline": True,
            "why": "Necesitamos la barrera concreta de la EPS para sostener el caso.",
        }
    if workflow_type == "tutela" and not _text(intake.get("prior_tutela")):
        return {
            "id": "prior_tutela",
            "question": "Ya habias presentado otra tutela por este mismo problema?",
            "placeholder": "Responde si o no y, si hubo una anterior, cuenta que paso.",
            "multiline": True,
            "why": "Hay que dejar clara la no temeridad o la existencia de una tutela previa.",
        }
    return None


def build_health_agent_state(
    *,
    category: str,
    workflow_type: str,
    recommended_action: str,
    description: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    if _lower(category) != "salud":
        return {}

    intake = facts.get("intake_form") or {}
    attachment_context = facts.get("attachment_intelligence") or {}
    combined_text = _join_texts(
        description,
        facts.get("hechos_principales"),
        intake.get("case_story"),
        intake.get("concrete_request"),
        intake.get("urgency_detail"),
        intake.get("ongoing_harm"),
        intake.get("eps_response_detail"),
        intake.get("tutela_other_means_detail"),
        attachment_context.get("combined_text"),
    )
    lowered = _lower(combined_text)
    uploaded_files = facts.get("uploaded_evidence_files") or []
    attachment_names = attachment_context.get("evidence_names") or []
    document_profile = resolve_health_document(workflow_type=workflow_type, recommended_action=recommended_action)

    target_entity = _text(intake.get("target_entity") or intake.get("eps_name"))
    diagnosis = _text(intake.get("diagnosis"))
    treatment_needed = _text(intake.get("treatment_needed"))
    has_medical_support = (
        bool(uploaded_files)
        or bool(attachment_names)
        or bool(_text(intake.get("medical_order_date")))
        or bool(_text(intake.get("treating_doctor_name")))
    )
    has_barrier_context = any(
        _text(intake.get(field))
        for field in ("eps_response_detail", "eps_request_date", "eps_request_reference", "eps_request_channel", "tutela_other_means_detail")
    ) or _lower(intake.get("prior_claim")) in {"si", "sí", "no", "aun no", "aún no", "no_aun_no"} or _has_any(
        lowered,
        ["nego", "negó", "silencio", "sin respuesta", "demoro", "demoró", "no agendo", "no autorizo", "no autorizó", "barrera", "eps"],
    )
    has_risk_context = any(
        _text(intake.get(field))
        for field in ("urgency_detail", "ongoing_harm", "tutela_immediacy_detail", "tutela_special_protection_detail")
    ) or _lower(intake.get("special_protection")) not in {"", "no aplica", "ninguno"} or _has_any(
        lowered,
        ["riesgo", "dolor", "empeor", "crisis", "urgente", "urgencia", "hospital", "sin medicamento", "sin tratamiento", "sin examen"],
    )

    next_prompt = _build_next_prompt(intake=intake, facts=facts, workflow_type=workflow_type)
    user_owned_missing: list[str] = []
    if next_prompt:
        user_owned_missing.append(next_prompt["why"])

    can_generate = bool(target_entity and diagnosis and treatment_needed and has_medical_support and (has_barrier_context or workflow_type != "tutela"))
    if workflow_type == "tutela":
        can_generate = can_generate and bool(
            has_risk_context
            or has_barrier_context
            or _lower(intake.get("special_protection")) not in {"", "no aplica", "ninguno"}
        )

    inferred_risk = []
    if _lower(intake.get("special_protection")) not in {"", "no aplica", "ninguno"}:
        inferred_risk.append(f"Proteccion especial detectada: {_text(intake.get('special_protection'))}")
    if _text(intake.get("urgency_detail")):
        inferred_risk.append(_text(intake.get("urgency_detail")))
    elif has_risk_context:
        inferred_risk.append("Los soportes y el relato ya permiten inferir riesgo actual o afectacion en curso.")

    inferred_barrier = []
    if _text(intake.get("eps_response_detail")):
        inferred_barrier.append(_text(intake.get("eps_response_detail")))
    elif has_barrier_context:
        inferred_barrier.append("La IA ya puede reconstruir la barrera de la EPS con el relato, fechas y anexos cargados.")

    ready_state = can_generate
    summary = (
        "El agente ya tiene base suficiente del bloque salud. Puede generar el documento ahora y seguir recibiendo datos adicionales por chat."
        if ready_state
        else (
            "El agente necesita un ultimo dato factual del bloque salud antes de redactar."
            if next_prompt
            else "El agente sigue activo y puede recibir mas datos para terminar de consolidar el expediente."
        )
    )

    return {
        "enabled": True,
        "block": "salud",
        "mode": "chat",
        "agent_is_live": True,
        "document_profile": document_profile.to_dict(),
        "documents_available": list_health_block_documents(),
        "status": "ready" if ready_state else ("collecting" if next_prompt else "active"),
        "can_generate": can_generate,
        "next_prompt": None if ready_state else next_prompt,
        "optional_prompt": next_prompt if ready_state else None,
        "user_owned_missing": [] if ready_state else user_owned_missing,
        "ai_owned_tasks": [
            "Identificar y redactar el riesgo actual del paciente",
            "Reconstruir la barrera concreta de la EPS o IPS",
            "Explicar urgencia, procedencia y argumentacion juridica",
        ],
        "known_facts": {
            "target_entity": target_entity,
            "diagnosis": diagnosis,
            "treatment_needed": treatment_needed,
            "medical_support_loaded": bool(uploaded_files),
            "has_barrier_context": has_barrier_context,
            "has_risk_context": has_risk_context,
        },
        "analysis": {
            "risk_summary": inferred_risk,
            "barrier_summary": inferred_barrier,
            "files_count": len(uploaded_files) or len(attachment_names),
        },
        "summary": summary,
    }


def relax_health_tutela_blockers(blocking_issues: list[str], facts: dict[str, Any]) -> list[str]:
    agent_state = facts.get("agent_state") or {}
    if agent_state.get("block") != "salud" or not agent_state.get("can_generate"):
        return blocking_issues

    suppress_patterns = (
        "subsidiariedad",
        "perjuicio irremediable",
        "inmediatez",
        "hechos actuales del paciente",
        "barrera de la eps",
        "riesgo que sigue ocurriendo hoy",
        "declaracion de no temeridad",
        "declaracion de no temeridad",
        "otra tutela",
    )
    return [issue for issue in blocking_issues if not any(pattern in _lower(issue) for pattern in suppress_patterns)]
