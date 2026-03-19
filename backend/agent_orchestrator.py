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


def _looks_partial_person_name(value: str) -> bool:
    text = _text(value)
    if not text:
        return False
    parts = [part for part in re.split(r"\s+", text) if part]
    if len(parts) <= 1:
        return True
    return sum(1 for part in parts if len(part) > 1) < 2


def _represented_identity_is_complete(*, name: str, age_or_birth: str, document: str) -> bool:
    if _looks_partial_person_name(name):
        return False
    if not _text(age_or_birth):
        return False
    return bool(_text(document))


def _build_next_prompt(*, intake: dict[str, Any], facts: dict[str, Any], workflow_type: str) -> dict[str, Any] | None:
    acting_capacity = _lower(intake.get("acting_capacity"))
    target_entity = _text(intake.get("target_entity"))
    eps_name = _text(intake.get("eps_name"))
    prior_claim = _lower(intake.get("prior_claim"))
    prior_claim_detail = _text(intake.get("prior_claim_result") or intake.get("eps_response_detail") or intake.get("tutela_other_means_detail"))
    attachment_suggestions = ((facts.get("attachment_intelligence") or {}).get("typed_suggestions") or {})
    represented_person_name = _text(intake.get("represented_person_name")) or _text(attachment_suggestions.get("represented_person_name"))
    represented_person_age = (
        _text(intake.get("represented_person_age"))
        or _text(intake.get("represented_person_birth_date"))
        or _text(attachment_suggestions.get("represented_person_age"))
        or _text(attachment_suggestions.get("represented_person_birth_date"))
    )
    represented_person_document = _text(intake.get("represented_person_document")) or _text(attachment_suggestions.get("represented_person_document"))
    identity_support_unreadable = _lower(attachment_suggestions.get("identity_support_unreadable")) == "si"
    special_protection = _lower(intake.get("special_protection"))
    continuity_text = _join_texts(intake.get("treatment_needed"), intake.get("urgency_detail"), intake.get("ongoing_harm"), facts.get("hechos_principales"))
    continuity_case = _has_any(_lower(continuity_text), ["continuidad", "sin medicamento", "sin tratamiento", "suspension", "suspensión", "interrupcion", "interrupción", "quimioterapia", "dialisis", "diálisis"])
    if target_entity and eps_name and _lower(target_entity) != _lower(eps_name):
        return {
            "id": "target_entity",
            "question": f"Veo dos entidades distintas en el caso: '{target_entity}' y '{eps_name}'. Cual es la EPS o IPS correcta contra la que va el documento?",
            "placeholder": "Escribe un solo nombre oficial de la EPS o IPS correcta",
            "multiline": False,
            "why": "La entidad accionada esta inconsistente y debe quedar unica antes de redactar.",
        }
    if prior_claim in {"no", "aun no", "aún no", "no_aun_no"} and prior_claim_detail:
        return {
            "id": "prior_claim",
            "question": "Marcaste que no habia gestion previa, pero el relato si menciona solicitud, radicado o respuesta de la EPS. Confirma cual de las dos versiones es la correcta.",
            "placeholder": "Ej: si hubo PQRS el 3 de marzo y respondieron..., o no hubo ninguna gestion previa",
            "multiline": True,
            "why": "La via previa del caso esta contradictoria y hay que corregirla antes de cerrar la procedencia.",
        }
    if acting_capacity == "nombre_propio" and (represented_person_name or represented_person_age or represented_person_document):
        return {
            "id": "acting_capacity",
            "question": "El expediente trae datos de un menor o representado, pero la calidad del accionante sigue en nombre propio. Confirma si presentas el caso por ti o por otra persona.",
            "placeholder": "Ej: madre del menor / padre / agente oficioso / nombre propio",
            "multiline": False,
            "why": "Hay que aclarar quien es la persona protegida y en que calidad actua quien presenta el caso.",
        }
    if acting_capacity and acting_capacity != "nombre_propio" and not represented_person_name:
        return {
            "id": "represented_person_name",
            "question": "Como se llama el paciente o la persona afectada por quien presentas este caso?",
            "placeholder": "Ej: Jeronimo Perez",
            "multiline": False,
            "why": "Necesitamos identificar claramente a la persona protegida en el documento.",
        }
    if acting_capacity and acting_capacity != "nombre_propio" and (not represented_person_age or _looks_partial_person_name(represented_person_name) or identity_support_unreadable):
        return {
            "id": "represented_person_identity",
            "question": "Confirma la identificacion completa del menor o representado: nombre completo, edad o fecha de nacimiento y, si la tienes, numero de documento.",
            "placeholder": "Ej: Jeronimo Perez Lopez, 10 anos, nacido el 14/05/2015, TI 1022334455",
            "multiline": False,
            "why": "La tutela debe identificar con precision al menor o representado protegido por el juez.",
        }
    if acting_capacity and acting_capacity != "nombre_propio" and represented_person_name and not represented_person_document:
        return {
            "id": "represented_person_document",
            "question": "Si la tienes a la mano, cual es la tarjeta de identidad, NUIP o documento del menor o representado?",
            "placeholder": "Ej: TI 1022334455",
            "multiline": False,
            "why": "Esto mejora la identificacion exacta del paciente en el documento.",
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
    if continuity_case and not _text(intake.get("ongoing_harm")):
        return {
            "id": "ongoing_harm",
            "question": "Explica que pasa si se interrumpe ese tratamiento o si siguen sin entregar el servicio hoy.",
            "placeholder": "Ej: aumenta el dolor, reaparecen crisis, se pierde continuidad clinica o hay riesgo de complicacion",
            "multiline": True,
            "why": "La continuidad del tratamiento debe quedar explicada como riesgo actual para sostener mejor la tutela en salud.",
        }
    if special_protection not in {"", "no aplica", "ninguno"} and not _text(intake.get("tutela_special_protection_detail")):
        return {
            "id": "tutela_special_protection_detail",
            "question": "Cuenta por que el paciente tiene especial proteccion y como esa condicion agrava la urgencia del caso.",
            "placeholder": "Ej: es menor de edad, esta embarazada, tiene discapacidad o enfermedad grave y no puede esperar",
            "multiline": True,
            "why": "La proteccion reforzada ayuda a justificar por que este caso no deberia esperar otra gestion.",
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
    attachment_suggestions = (attachment_context.get("typed_suggestions") or {})
    acting_capacity = _lower(intake.get("acting_capacity"))
    represented_person_name = _text(intake.get("represented_person_name")) or _text(attachment_suggestions.get("represented_person_name"))
    represented_person_age = (
        _text(intake.get("represented_person_age"))
        or _text(intake.get("represented_person_birth_date"))
        or _text(attachment_suggestions.get("represented_person_age"))
        or _text(attachment_suggestions.get("represented_person_birth_date"))
    )
    represented_person_document = _text(intake.get("represented_person_document")) or _text(attachment_suggestions.get("represented_person_document"))

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
    has_continuity_context = _has_any(
        lowered,
        ["continuidad", "sin medicamento", "sin tratamiento", "suspension", "suspensión", "interrupcion", "interrupción", "quimioterapia", "dialisis", "diálisis"],
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
            or has_continuity_context
            or _lower(intake.get("special_protection")) not in {"", "no aplica", "ninguno"}
        )
    if workflow_type == "tutela" and acting_capacity and acting_capacity != "nombre_propio":
        can_generate = can_generate and _represented_identity_is_complete(
            name=represented_person_name,
            age_or_birth=represented_person_age,
            document=represented_person_document,
        )

    inferred_risk = []
    if _lower(intake.get("special_protection")) not in {"", "no aplica", "ninguno"}:
        inferred_risk.append(f"Proteccion especial detectada: {_text(intake.get('special_protection'))}")
    if _text(intake.get("urgency_detail")):
        inferred_risk.append(_text(intake.get("urgency_detail")))
    elif has_risk_context:
        inferred_risk.append("Los soportes y el relato ya permiten inferir riesgo actual o afectacion en curso.")
    if has_continuity_context:
        inferred_risk.append("Se detecta continuidad de tratamiento comprometida, lo que refuerza la urgencia del caso.")

    inferred_barrier = []
    if _text(intake.get("eps_response_detail")):
        inferred_barrier.append(_text(intake.get("eps_response_detail")))
    elif has_barrier_context:
        inferred_barrier.append("De la narracion del caso, las fechas relevantes y los soportes aportados se advierte una barrera administrativa atribuible a la EPS.")

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
