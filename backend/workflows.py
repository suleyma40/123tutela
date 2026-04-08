from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend import repository_ext as repository
from backend.config import settings
from backend.document_writer import build_document as build_document_from_template


CATEGORY_CONFIG: dict[str, dict[str, Any]] = {
    "Salud": {
        "module": "SALUD",
        "default_workflow": "derecho_peticion",
        "urgent_keywords": ["vida", "urgente", "cirugia", "riesgo", "uci", "menor", "embarazada"],
        "prerequisites": [
            {"id": "eps_pqrs", "label": "Radicar PQRS o derecho de petición ante la EPS", "required": True},
            {"id": "supersalud", "label": "Escalar a Supersalud cuando la PQRS no sea eficaz", "required": False},
        ],
    },
    "Laboral": {
        "module": "LABORAL",
        "default_workflow": "derecho_peticion",
        "urgent_keywords": ["minimo vital", "fuero", "embarazo", "discapacidad", "salud"],
        "prerequisites": [
            {"id": "reclamo_empleador", "label": "Reclamar directamente al empleador o pedir respuesta formal", "required": False},
        ],
    },
    "Bancos": {
        "module": "HABEAS DATA",
        "default_workflow": "reclamacion",
        "urgent_keywords": ["embargo", "bloqueo", "fraude", "suplantacion"],
        "prerequisites": [
            {"id": "reclamo_banco", "label": "Presentar reclamación ante la entidad financiera", "required": True},
        ],
    },
    "Servicios": {
        "module": "SERVICIOS",
        "default_workflow": "reclamacion",
        "urgent_keywords": ["corte", "agua", "luz", "energia", "salud"],
        "prerequisites": [
            {"id": "reclamo_empresa", "label": "Presentar reclamación previa ante la empresa de servicios", "required": True},
        ],
    },
    "Consumidor": {
        "module": "CONSUMIDOR",
        "default_workflow": "reclamacion",
        "urgent_keywords": ["garantia", "reembolso", "incumplimiento"],
        "prerequisites": [
            {"id": "reclamo_comercio", "label": "Solicitar respuesta al comercio o proveedor", "required": True},
        ],
    },
    "Datos": {
        "module": "HABEAS DATA",
        "default_workflow": "reclamacion",
        "urgent_keywords": ["datacredito", "cifin", "reporte", "fraude", "suplantacion"],
        "prerequisites": [
            {"id": "reclamo_fuente", "label": "Reclamar ante la fuente o central de riesgo", "required": True},
        ],
    },
}


def user_profile_complete(user: dict[str, Any]) -> bool:
    required = [
        user.get("name"),
        user.get("document_number"),
        user.get("phone"),
        user.get("city"),
        user.get("department"),
        user.get("address"),
    ]
    return all(isinstance(value, str) and value.strip() for value in required)


def _contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _health_intake_text(facts: dict[str, Any], *keys: str) -> str:
    intake = (facts or {}).get("intake_form") or {}
    for key in keys:
        value = _text(intake.get(key))
        if value:
            return value
    return ""


def _contains_health_urgency_signal(text: str) -> bool:
    negative_markers = [
        "no es una urgencia",
        "no hay urgencia",
        "no es urgente",
        "sin urgencia",
        "no hay un riesgo vital",
        "no existe riesgo vital",
        "ya no hay urgencia",
        "ya no hay una urgencia",
        "ya no hay una urgencia actual",
        "ya no existe urgencia",
    ]
    if any(marker in text for marker in negative_markers):
        return False
    return _contains_any(
        text,
        [
            "urgencia",
            "grave",
            "riesgo",
            "perjuicio irremediable",
            "vida",
            "dolor",
            "agrav",
            "empeor",
            "uci",
            "cirugia",
            "cirugía",
            "hospitalizacion",
            "hospitalización",
            "crisis",
        ],
    )


def _contains_health_continuity_signal(text: str) -> bool:
    return _contains_any(
        text,
        [
            "continuidad del tratamiento",
            "sin medicamento",
            "sin tratamiento",
            "suspension del tratamiento",
            "suspensión del tratamiento",
            "interrupcion del tratamiento",
            "interrupción del tratamiento",
            "dosis pendiente",
            "quimioterapia",
            "dialisis",
            "diálisis",
            "terapia continua",
            "control prioritario",
            "seguimiento oncologico",
            "seguimiento oncológico",
        ],
    )


def _contains_special_protection_signal(text: str) -> bool:
    return _contains_any(
        text,
        [
            "menor",
            "menor de edad",
            "nino",
            "niño",
            "nina",
            "niña",
            "adolescente",
            "embarazada",
            "gestante",
            "adulto mayor",
            "discapacidad",
            "cancer",
            "cáncer",
            "enfermedad huerfana",
            "enfermedad huérfana",
        ],
    )


def _health_text_supports_urgency(*parts: str) -> bool:
    joined = " ".join(part for part in parts if part).lower()
    if not joined:
        return False
    return _contains_health_urgency_signal(joined) or _contains_health_continuity_signal(joined)


def _contains_health_resolved_signal(text: str) -> bool:
    return _contains_any(
        text,
        [
            "ya autorizo",
            "ya autorizó",
            "ya autorizaron",
            "ya programo",
            "ya programó",
            "ya programaron",
            "ya agendaron",
            "ya entregaron",
            "ya resolvieron",
            "caso resuelto",
            "problema resuelto",
            "ya emitio autorizacion",
            "ya emitió autorización",
        ],
    )


def _infer_health_workflow(
    *,
    facts: dict[str, Any],
    lowered: str,
    prior_actions: list[str],
    all_required_done: bool,
    urgent: bool,
) -> tuple[str, str, list[str]]:
    intake = (facts or {}).get("intake_form") or {}
    warnings: list[str] = []

    target_entity = _health_intake_text(facts, "target_entity", "eps_name")
    diagnosis = _health_intake_text(facts, "diagnosis")
    treatment_needed = _health_intake_text(facts, "treatment_needed")
    urgency_detail = _health_intake_text(facts, "urgency_detail", "current_harm", "ongoing_harm", "tutela_immediacy_detail")
    prior_claim = _lower(intake.get("prior_claim"))
    prior_claim_result = _health_intake_text(facts, "prior_claim_result", "eps_response_detail", "tutela_other_means_detail")
    tutela_ruling_date = _health_intake_text(facts, "tutela_ruling_date")
    tutela_order_summary = _health_intake_text(facts, "tutela_order_summary")
    tutela_decision_result = _health_intake_text(facts, "tutela_decision_result")
    tutela_appeal_reason = _health_intake_text(facts, "tutela_appeal_reason")
    tutela_noncompliance_detail = _health_intake_text(facts, "tutela_noncompliance_detail")
    special_protection = _lower(intake.get("special_protection") or intake.get("tutela_special_protection_detail"))
    current_harm = _health_intake_text(facts, "current_harm", "ongoing_harm", "urgency_detail", "tutela_immediacy_detail")
    continuity_detail = _health_intake_text(facts, "treatment_needed", "urgency_detail", "current_harm", "ongoing_harm")

    has_health_core = bool(target_entity and (diagnosis or treatment_needed))
    has_medical_support = bool(
        _health_intake_text(facts, "medical_order_date", "treating_doctor_name", "supporting_documents", "evidence_summary")
    ) or _contains_any(lowered, ["orden medica", "formula", "historia clinica", "historia clínica", "medico", "médico"])
    has_barrier = bool(prior_claim_result or _health_intake_text(facts, "eps_request_date", "eps_request_reference")) or _contains_any(
        lowered,
        ["negar", "negaron", "negada", "demora", "demoraron", "silencio", "sin respuesta", "no autorizan", "no autorizan", "no entregan", "no entregaron", "barrera", "suspendieron", "no agendan", "eps", "ips"],
    )
    has_continuity_risk = bool(continuity_detail) and _contains_health_continuity_signal(_lower(continuity_detail) + " " + lowered)
    has_urgency = _health_text_supports_urgency(urgency_detail, current_harm, lowered) or urgent or has_continuity_risk
    has_special_protection = special_protection not in {"", "no aplica", "ninguno"} or _contains_special_protection_signal(lowered)
    has_resolved_signal = _contains_health_resolved_signal(lowered)
    prior_claim_done = all_required_done or bool(prior_actions) or prior_claim in {"si", "sí", "reclame", "reclamo", "radicado"} or bool(
        _health_intake_text(facts, "eps_request_date", "eps_request_reference", "eps_request_channel")
    )
    urgency_without_waiting = has_urgency and (has_special_protection or has_continuity_risk or _contains_health_urgency_signal(_lower(current_harm) + " " + lowered))

    has_prior_ruling = bool(tutela_ruling_date or tutela_order_summary or tutela_decision_result) or _contains_any(
        lowered,
        ["fallo de tutela", "sentencia de tutela", "juzgado", "despacho", "decision de tutela", "decisión de tutela"],
    )
    has_desacato_signal = bool(tutela_noncompliance_detail) or _contains_any(
        lowered,
        ["desacato", "incumplimiento del fallo", "no ha cumplido el fallo", "sigue sin cumplir", "orden judicial incumplida"],
    )
    has_impugnacion_signal = bool(tutela_appeal_reason) or _contains_any(
        lowered,
        ["impugnacion", "impugnación", "impugnar", "fallo negado", "fallo improcedente", "decision injusta", "decisión injusta"],
    )

    if has_prior_ruling and has_desacato_signal:
        return "desacato", "Incidente de desacato", warnings
    if has_prior_ruling and has_impugnacion_signal:
        return "impugnacion", "Impugnacion de tutela", warnings

    if has_resolved_signal and not has_continuity_risk and not urgency_without_waiting:
        warnings.append("El relato sugiere que la barrera principal ya fue superada; conviene revisar si el caso sigue vivo o si ahora corresponde solo trazabilidad, peticion o seguimiento.")
        return "derecho_peticion", "Derecho de peticion a EPS", warnings

    if has_health_core and has_barrier and has_medical_support and (has_urgency or has_special_protection):
        if not prior_claim_done:
            if urgency_without_waiting:
                warnings.append("Se recomienda tutela en salud aunque la via previa no este completa, porque el expediente muestra urgencia reforzada o continuidad de tratamiento que no deberia esperar.")
            else:
                warnings.append("Se recomienda tutela por urgencia en salud, pero conviene dejar mejor explicada la gestion previa ante la EPS o por que no era exigible esperar.")
        return "tutela", "Accion de tutela", warnings

    if has_health_core and has_barrier and prior_claim_done:
        warnings.append("Se conserva derecho de peticion como ruta inicial mientras se refuerza la urgencia o el dano actual para una tutela en salud.")
        return "derecho_peticion", "Derecho de peticion a EPS", warnings

    warnings.append("Antes de tutela en salud, la via previa ante EPS debe quedar documentada salvo urgencia manifiesta.")
    return "derecho_peticion", "Derecho de peticion a EPS", warnings


def normalize_prior_actions(prior_actions: list[str], category: str) -> list[dict[str, Any]]:
    config = CATEGORY_CONFIG.get(category, {})
    completed = set(prior_actions)
    return [
        {
            **item,
            "completed": item["id"] in completed,
        }
        for item in config.get("prerequisites", [])
    ]


def infer_workflow(
    *,
    category: str,
    description: str,
    facts: dict[str, Any],
    legal_analysis: dict[str, Any],
    prior_actions: list[str],
) -> dict[str, Any]:
    config = CATEGORY_CONFIG.get(category, {"module": category.upper(), "default_workflow": "reclamacion", "urgent_keywords": [], "prerequisites": []})
    lowered = f"{description} {facts.get('problema_central', '')}".lower()
    prerequisites = normalize_prior_actions(prior_actions, category)
    all_required_done = all(item["completed"] for item in prerequisites if item.get("required"))
    urgent = any(keyword in lowered for keyword in config.get("urgent_keywords", []))
    rights = legal_analysis.get("derechos_vulnerados") or []
    warnings: list[str] = []

    workflow_type = config["default_workflow"]
    recommended_action = legal_analysis.get("recommended_action") or "Reclamacion"
    has_habeas_signal = _contains_any(lowered, ["habeas", "datacredito", "cifin", "reporte", "central de riesgo", "dato personal"])
    has_petition_signal = _contains_any(lowered, ["derecho de peticion", "derecho de petición", "respondan", "entreguen", "informacion", "información", "documentos", "consulta", "certifiquen"])
    has_complaint_signal = _contains_any(lowered, ["queja", "reclamo", "garantia", "garantía", "devolucion", "devolución", "factura", "cobro", "bloqueo", "corte", "incumplimiento"])
    has_tutela_signal = _contains_any(lowered, ["tutela", "derecho fundamental", "minimo vital", "mínimo vital", "vida", "salud", "urgencia", "riesgo", "perjuicio irremediable"])

    if category == "Salud":
        workflow_type, recommended_action, health_warnings = _infer_health_workflow(
            facts=facts,
            lowered=lowered,
            prior_actions=prior_actions,
            all_required_done=all_required_done,
            urgent=urgent,
        )
        warnings.extend(health_warnings)
    elif category == "Datos":
        if all_required_done and has_habeas_signal:
            workflow_type = "tutela"
            recommended_action = "Accion de tutela por habeas data"
        else:
            workflow_type = "reclamacion"
            recommended_action = "Reclamacion de habeas data"
            warnings.append("La tutela en habeas data se reserva para cuando la reclamacion previa no resuelve o existe afectacion grave.")
    elif category == "Laboral":
        if urgent or "minimo vital" in lowered or "mínimo vital" in lowered or has_tutela_signal:
            workflow_type = "tutela"
            recommended_action = "Accion de tutela"
        else:
            workflow_type = "derecho_peticion"
            recommended_action = "Derecho de peticion laboral"
    elif category == "Bancos":
        if has_habeas_signal:
            if all_required_done and (urgent or has_tutela_signal):
                workflow_type = "tutela"
                recommended_action = "Accion de tutela por habeas data"
            else:
                workflow_type = "reclamacion"
                recommended_action = "Reclamacion de habeas data"
                warnings.append("En bancos, los reportes y datos negativos suelen exigir reclamacion previa antes de escalar a tutela.")
        elif all_required_done and urgent:
            workflow_type = "tutela"
            recommended_action = "Accion de tutela"
        elif has_petition_signal:
            workflow_type = "derecho_peticion"
            recommended_action = "Derecho de peticion financiero"
        else:
            workflow_type = "reclamacion"
            recommended_action = "Reclamacion financiera"
            if not all_required_done:
                warnings.append("Debes agotar la reclamacion directa ante la entidad financiera antes de escalar a tutela salvo vulneracion urgente.")
    elif category == "Servicios":
        if all_required_done and urgent:
            workflow_type = "tutela"
            recommended_action = "Accion de tutela"
        elif has_petition_signal:
            workflow_type = "derecho_peticion"
            recommended_action = "Derecho de peticion a empresa de servicios"
        else:
            workflow_type = "reclamacion"
            recommended_action = "Reclamacion por servicios publicos"
            if not all_required_done:
                warnings.append("Debes agotar la reclamacion directa ante la empresa de servicios antes de escalar a tutela salvo afectacion urgente.")
    elif category == "Consumidor":
        if all_required_done and urgent:
            workflow_type = "tutela"
            recommended_action = "Accion de tutela"
        elif has_petition_signal:
            workflow_type = "derecho_peticion"
            recommended_action = "Derecho de peticion al proveedor"
        elif has_complaint_signal:
            workflow_type = "reclamacion"
            recommended_action = "Reclamo de consumo"
        else:
            workflow_type = "reclamacion"
            recommended_action = "Queja o reclamo al proveedor"
            if not all_required_done:
                warnings.append("Antes de escalar un conflicto de consumo, conviene dejar trazabilidad de la reclamacion directa al proveedor.")

    if rights and workflow_type != "tutela" and any("fundamental" in str(item).lower() for item in rights):
        warnings.append("Se detectaron derechos fundamentales comprometidos, pero el flujo conserva la via previa exigida por la operacion.")

    legal_analysis["recommended_action"] = recommended_action
    return {
        "module": config["module"],
        "workflow_type": workflow_type,
        "recommended_action": recommended_action,
        "prerequisites": prerequisites,
        "warnings": warnings,
    }


def _rule_lookup() -> dict[str, dict[str, Any]]:
    rules = repository.list_business_rules()
    return {str(rule.get("rule_key")): rule for rule in rules}


def _build_target_from_court(court: dict[str, Any]) -> dict[str, Any]:
    contact = court.get("url_referencia") or court.get("correo_reparto")
    channel = "portal" if court.get("url_referencia") else "email"
    generates_radicado = bool(court.get("codigo_interno") == "NAC-001" or court.get("plataforma_oficial"))
    return {
        "type": "juzgado",
        "name": court.get("tipo_oficina") or court.get("municipio") or "Rama Judicial",
        "channel": channel,
        "contact": contact,
        "email": court.get("correo_reparto"),
        "alternate_contact": court.get("correo_alternativo"),
        "automatable": channel in {"portal", "email"},
        "genera_radicado": generates_radicado,
        "subject_suggested": court.get("asunto_recomendado"),
        "reason": "Tutela priorizada con base en correo o portal judicial verificado.",
        "metadata": {
            "codigo": court.get("codigo_interno"),
            "municipio": court.get("municipio"),
            "departamento": court.get("departamento"),
            "plataforma": court.get("plataforma_oficial"),
            "notas": court.get("notas"),
        },
    }


def _build_target_from_entity(match: dict[str, Any]) -> dict[str, Any]:
    channel = (match.get("canal_envio") or "").lower()
    contact = match.get("contacto_envio")
    normalized_channel = "email" if "mail" in channel or "correo" in channel else "portal" if "web" in channel or "portal" in channel else "manual"
    return {
        "type": "entidad",
        "name": match.get("nombre_entidad"),
        "channel": normalized_channel,
        "contact": contact,
        "automatable": normalized_channel in {"email", "portal"} and bool(contact),
        "genera_radicado": bool(match.get("genera_radicado")),
        "subject_suggested": None,
        "reason": "Entidad sugerida desde la base operativa del módulo.",
        "metadata": {
            "modulo": match.get("modulo"),
            "paso_flujo": match.get("paso_flujo"),
            "plazo_respuesta": match.get("plazo_respuesta"),
            "observaciones": match.get("observaciones"),
        },
    }


def _build_target_from_intake(facts: dict[str, Any], recommended_action: str) -> dict[str, Any] | None:
    intake = (facts or {}).get("intake_form") or {}
    entity_name = str(intake.get("target_entity") or "").strip()
    if not entity_name:
        return None

    contact = (
        intake.get("target_pqrs_email")
        or intake.get("target_notification_email")
        or intake.get("target_website")
        or intake.get("target_phone")
    )
    contact = str(contact or "").strip() or None
    channel = "manual"
    if contact:
        if "@" in contact:
            channel = "email"
        elif str(contact).lower().startswith("http"):
            channel = "portal"

    metadata = {
        "nit": intake.get("target_identifier"),
        "address": intake.get("target_address"),
        "legal_representative": intake.get("legal_representative"),
        "superintendence": intake.get("target_superintendence"),
        "website": intake.get("target_website"),
        "phone": intake.get("target_phone"),
    }
    return {
        "type": "entidad",
        "name": entity_name,
        "channel": channel,
        "contact": contact,
        "automatable": channel in {"email", "portal"} and bool(contact),
        "genera_radicado": channel in {"email", "portal"},
        "subject_suggested": f"{recommended_action} - {entity_name}",
        "reason": "Entidad consolidada desde el formulario completado por la persona usuaria.",
        "metadata": metadata,
    }


def _judicial_target_scope(target: dict[str, Any] | None, city: str, department: str) -> str:
    if not target or _lower(target.get("type")) != "juzgado":
        return "non_judicial"
    metadata = target.get("metadata") or {}
    target_city = _lower(metadata.get("municipio"))
    target_department = _lower(metadata.get("departamento"))
    code = _lower(metadata.get("codigo"))
    if code == "nac-001":
        return "national"
    if target_city and target_city == _lower(city):
        return "local"
    if target_department and target_department == _lower(department):
        return "department"
    return "mismatch"


def _judicial_territorial_note(target: dict[str, Any] | None, city: str, department: str) -> str | None:
    scope = _judicial_target_scope(target, city, department)
    metadata = (target or {}).get("metadata") or {}
    target_city = metadata.get("municipio")
    target_department = metadata.get("departamento")
    if scope == "local":
        return f"Se priorizo un canal judicial de {city}."
    if scope == "department":
        return f"No encontramos un canal exacto para {city}; se priorizo un canal judicial de {department}."
    if scope == "national":
        return "No encontramos un canal territorial mejor posicionado y se uso el fallback nacional oficial."
    if scope == "mismatch":
        return (
            f"El destino judicial sugerido pertenece a {target_city or 'otro municipio'}"
            f"{', ' + target_department if target_department else ''}. Revisa este destino antes de enviar."
        )
    return None


def build_routing(
    *,
    category: str,
    city: str,
    department: str,
    facts: dict[str, Any],
    workflow_type: str,
    recommended_action: str,
) -> dict[str, Any]:
    entities = facts.get("entidades_involucradas") or facts.get("entities") or []
    entity_names = [str(item).strip() for item in entities if str(item).strip()]
    rules = _rule_lookup()

    judicial_workflows = {"tutela", "impugnacion", "desacato"}
    targets: list[dict[str, Any]] = []
    if workflow_type in judicial_workflows:
        targets.extend(_build_target_from_court(item) for item in repository.search_court_targets(city, department))
    else:
        intake_target = _build_target_from_intake(facts, recommended_action)
        entity_targets = [_build_target_from_entity(item) for item in repository.search_entities(category, entity_names)]
        entity_targets = [item for item in entity_targets if item.get("name")]
        if intake_target and intake_target.get("contact"):
            targets.append(intake_target)
        targets.extend(entity_targets)
        if intake_target and not intake_target.get("contact"):
            targets.append(intake_target)

    primary_target = targets[0] if targets else None
    fallback_mode = "none"
    fallback_instructions: list[str] = []

    if not primary_target or not primary_target.get("contact"):
        fallback_mode = "ask_user_contact"
        fallback_instructions = [
            "La entidad no tiene canal digital verificado en la base actual.",
            "Solicita al usuario un correo o dirección confiable antes de continuar.",
            "Si no existe información, cambia a modo presencial y pide evidencia posterior.",
        ]
    elif not primary_target.get("automatable"):
        fallback_mode = "presencial"
        fallback_instructions = [
            "La base indica que el canal es manual o presencial.",
            "Entrega instrucciones de impresión y solicita cargar foto/PDF del soporte radicado.",
        ]

    subject = primary_target.get("subject_suggested") if primary_target else None
    if not subject:
        subject = f"{recommended_action} - {category} - {city}, {department}"

    applied_rules = [
        {
            "rule_key": key,
            "title": rule.get("title"),
            "summary": rule.get("description"),
        }
        for key, rule in rules.items()
        if key in {"rule-copy-user", "rule-missing-channel", "decision-step-2", "decision-step-5"}
    ]

    return {
        "primary_target": primary_target,
        "secondary_targets": targets[1:4],
        "channel": primary_target.get("channel") if primary_target else "manual",
        "automatable": bool(primary_target and primary_target.get("automatable")),
        "genera_radicado": bool(primary_target and primary_target.get("genera_radicado")),
        "target_scope": _judicial_target_scope(primary_target, city, department),
        "territorial_match": _judicial_target_scope(primary_target, city, department) != "mismatch",
        "territorial_note": _judicial_territorial_note(primary_target, city, department),
        "subject": subject,
        "fallback": {
            "mode": fallback_mode,
            "instructions": fallback_instructions,
        },
        "applied_rules": applied_rules,
        "detected_entities": entity_names,
        "city": city,
        "department": department,
    }


def build_strategy_text(
    *,
    workflow_type: str,
    recommended_action: str,
    legal_analysis: dict[str, Any],
    warnings: list[str],
) -> str:
    rights = legal_analysis.get("derechos_vulnerados") or []
    rules = legal_analysis.get("normas_relevantes") or []
    rights_text = ", ".join(rights) if isinstance(rights, list) else str(rights)
    rules_text = ", ".join(rules) if isinstance(rules, list) else str(rules)
    warning_text = f" Advertencias operativas: {' | '.join(warnings)}." if warnings else ""
    return (
        f"La ruta sugerida es {recommended_action} ({workflow_type.replace('_', ' ')}). "
        f"Derechos identificados: {rights_text or 'pendientes de consolidar'}. "
        f"Soporte normativo principal: {rules_text or 'base normativa general cargada en la app'}."
        f"{warning_text}"
    )


def get_submission_policy(case: dict[str, Any]) -> dict[str, Any]:
    category = _lower(case.get("categoria") or case.get("category"))
    workflow_type = _lower(case.get("workflow_type"))
    recommended_action = _lower(case.get("recommended_action"))
    routing = case.get("routing") or {}
    automatable = bool(routing.get("automatable"))
    destination_channel = str((routing.get("primary_target") or {}).get("channel") or routing.get("channel") or "manual")
    primary_target = routing.get("primary_target") or {}
    requires_judicial_confirmation = str(primary_target.get("type") or "").lower() == "juzgado"

    if category != "salud":
        preferred_mode = "auto" if automatable else "manual_contact"
        return {
            "scope": "general",
            "allowed_modes": ["auto", "manual_contact", "presencial"],
            "preferred_mode": preferred_mode,
            "auto_allowed": automatable,
            "requires_assisted_filing": False,
            "customer_evidence_channels": ["panel", "email"] if case.get("usuario_email") else ["panel"],
            "minimum_internal_evidence": ["intento_de_radicacion", "canal_usado", "destino", "timestamp"],
            "minimum_customer_evidence": ["panel", "correo"] if case.get("usuario_email") else ["panel"],
            "summary": "La politica general permite envio automatico cuando existe canal confiable; de lo contrario, procede radicacion asistida o presencial.",
            "destination_channel": destination_channel,
            "requires_judicial_confirmation": requires_judicial_confirmation,
        }

    if "derecho de peticion" in recommended_action or workflow_type == "derecho_peticion":
        preferred_mode = "auto" if automatable else "manual_contact"
        return {
            "scope": "salud",
            "document_family": "derecho_peticion_salud",
            "allowed_modes": ["auto", "manual_contact", "presencial"],
            "preferred_mode": preferred_mode,
            "auto_allowed": automatable,
            "requires_assisted_filing": not automatable,
            "customer_evidence_channels": ["panel", "email"] if case.get("usuario_email") else ["panel"],
            "minimum_internal_evidence": ["correo_o_portal_destino", "acuse_o_radicado", "timestamp", "artefactos_firmados"],
            "minimum_customer_evidence": ["panel", "correo"] if case.get("usuario_email") else ["panel"],
            "summary": "El derecho de peticion en salud puede enviarse en automatico solo si existe un canal digital confiable de la entidad; en caso contrario, debe pasar a contacto asistido o presentacion presencial.",
            "destination_channel": destination_channel,
            "requires_judicial_confirmation": requires_judicial_confirmation,
        }

    if "impugnacion" in recommended_action or workflow_type == "impugnacion":
        preferred_mode = "auto" if automatable else "manual_contact"
        return {
            "scope": "salud",
            "document_family": "impugnacion_tutela_salud",
            "allowed_modes": ["auto", "manual_contact", "presencial"],
            "preferred_mode": preferred_mode,
            "auto_allowed": automatable,
            "requires_assisted_filing": not automatable,
            "customer_evidence_channels": ["panel", "email"] if case.get("usuario_email") else ["panel"],
            "minimum_internal_evidence": ["despacho_destino", "contacto_usado", "constancia_envio_o_radicado", "timestamp", "artefactos_firmados"],
            "minimum_customer_evidence": ["panel", "correo"] if case.get("usuario_email") else ["panel"],
            "summary": "La impugnacion de tutela en salud puede salir en automatico cuando exista un canal judicial confiable; en caso contrario, pasa a contacto asistido o presencial.",
            "destination_channel": destination_channel,
            "requires_judicial_confirmation": requires_judicial_confirmation,
        }

    if "desacato" in recommended_action or workflow_type == "desacato":
        preferred_mode = "auto" if automatable else "manual_contact"
        return {
            "scope": "salud",
            "document_family": "desacato_salud",
            "allowed_modes": ["auto", "manual_contact", "presencial"],
            "preferred_mode": preferred_mode,
            "auto_allowed": automatable,
            "requires_assisted_filing": not automatable,
            "customer_evidence_channels": ["panel", "email"] if case.get("usuario_email") else ["panel"],
            "minimum_internal_evidence": ["juzgado_origen", "contacto_usado", "constancia_envio_o_radicado", "timestamp", "artefactos_firmados"],
            "minimum_customer_evidence": ["panel", "correo"] if case.get("usuario_email") else ["panel"],
            "summary": "El incidente de desacato en salud puede salir en automatico cuando exista un canal judicial confiable; en caso contrario, pasa a contacto asistido o presencial.",
            "destination_channel": destination_channel,
            "requires_judicial_confirmation": requires_judicial_confirmation,
        }

    preferred_mode = "auto" if automatable else "manual_contact"
    return {
        "scope": "salud",
        "document_family": "tutela_salud",
        "allowed_modes": ["auto", "manual_contact", "presencial"],
        "preferred_mode": preferred_mode,
        "auto_allowed": automatable,
        "requires_assisted_filing": not automatable,
        "customer_evidence_channels": ["panel", "email"] if case.get("usuario_email") else ["panel"],
        "minimum_internal_evidence": ["despacho_destino", "contacto_usado", "constancia_envio_o_radicado", "timestamp", "artefactos_firmados"],
        "minimum_customer_evidence": ["panel", "correo"] if case.get("usuario_email") else ["panel"],
        "summary": "La accion de tutela en salud puede radicarse en automatico cuando exista un canal judicial confiable, incluido el correo nacional de reparto o correos judiciales de respaldo; si no, pasa a contacto asistido o presencial.",
        "destination_channel": destination_channel,
        "requires_judicial_confirmation": requires_judicial_confirmation,
    }


def build_submission_guidance(
    *,
    case: dict[str, Any],
    mode: str,
    channel: str,
    radicado: str | None,
) -> dict[str, Any]:
    workflow_type = str(case.get("workflow_type") or "")
    recommended_action = str(case.get("recommended_action") or "")
    user_email = case.get("usuario_email")
    user_phone = case.get("usuario_telefono")
    routing = case.get("routing") or {}
    submission_policy = get_submission_policy(case)
    proof_type = "constancia_manual"
    if radicado:
        proof_type = "numero_radicado"
    elif channel == "email":
        proof_type = "copia_correo"
    elif channel == "portal":
        proof_type = "acuse_portal"

    estimated_response_window = "Seguimiento interno pendiente de definir"
    if "tutela" in recommended_action.lower() or workflow_type == "tutela":
        estimated_response_window = "Respuesta judicial prioritaria; revisar novedades en horas o pocos dias segun reparto."
    elif "peticion" in recommended_action.lower():
        estimated_response_window = "Respuesta esperada segun Ley 1755 de 2015, de acuerdo con la modalidad de la peticion."
    elif "desacato" in recommended_action.lower():
        estimated_response_window = "Seguimiento judicial corto; revisar requerimientos del mismo juzgado de primera instancia."
    elif "impugnacion" in recommended_action.lower():
        estimated_response_window = "Revision de segunda instancia en los tiempos del despacho competente."

    next_step = "Seguir el caso desde el panel y esperar respuesta de la autoridad o entidad."
    continuity = ["seguimiento del caso"]
    follow_up_watch_items = [
        "Revisa si la entidad o el juzgado envia una respuesta, requerimiento o acuse.",
        "Si recibes una llamada, correo o mensaje por fuera del panel, reportalo en este mismo expediente.",
        "Conserva formulas, respuestas, acuses y cualquier soporte nuevo del caso.",
    ]
    escalation_triggers = [
        "Reporta cualquier novedad nueva para que el panel actualice el siguiente paso.",
    ]
    lowered_action = recommended_action.lower()
    if "tutela" in lowered_action:
        next_step = "Si niegan o limitan la tutela, evaluar impugnacion; si incumplen, evaluar desacato."
        continuity = ["seguimiento del caso", "impugnacion de tutela", "incidente de desacato"]
        follow_up_watch_items = [
            "Revisa si el juzgado admite, requiere informacion adicional o notifica fallo.",
            "Si el fallo sale desfavorable o incompleto, reportalo para evaluar impugnacion.",
            "Si el fallo sale favorable pero la orden no se cumple, reportalo para evaluar desacato.",
        ]
        escalation_triggers = [
            "Pasa a impugnacion si el fallo niega o limita la tutela.",
            "Pasa a desacato si existe fallo favorable y la orden sigue incumplida.",
        ]
    elif "peticion" in lowered_action:
        next_step = "Si no responden o responden de forma evasiva, evaluar tutela, reclamo o actuacion posterior."
        continuity = ["seguimiento del caso", "accion de tutela", "reclamo administrativo"]
        follow_up_watch_items = [
            "Espera respuesta de fondo de la EPS o entidad dentro del termino aplicable.",
            "Si responden de forma evasiva, parcial o negativa, sube esa respuesta al expediente.",
            "Si no responden dentro del termino, reportalo para evaluar tutela o actuacion posterior.",
        ]
        escalation_triggers = [
            "Pasa a tutela si persiste la barrera en salud con urgencia o riesgo actual.",
            "Pasa a una actuacion posterior si la respuesta fue evasiva, parcial o insuficiente.",
        ]
    elif "desacato" in lowered_action:
        next_step = "Monitorear cumplimiento efectivo del fallo y nuevas ordenes del juzgado."
        continuity = ["seguimiento del caso"]
        follow_up_watch_items = [
            "Revisa si el juzgado abre traslado, pide soporte adicional o dicta nuevas ordenes.",
            "Si la EPS cumple parcial o totalmente, reportalo en el expediente.",
            "Si el incumplimiento persiste, conserva evidencia actualizada del dano o barrera.",
        ]
        escalation_triggers = [
            "Reporta de inmediato cualquier cumplimiento parcial o nuevo incumplimiento.",
        ]
    elif "impugnacion" in lowered_action:
        next_step = "Esperar decision de segunda instancia y evaluar cumplimiento o desacato segun el resultado."
        continuity = ["seguimiento del caso", "incidente de desacato"]
        follow_up_watch_items = [
            "Revisa si llega decision de segunda instancia o requerimiento del despacho.",
            "Si la segunda instancia concede la tutela, verifica cumplimiento real de la orden.",
            "Si ya hay fallo favorable y no cumplen, reportalo para evaluar desacato.",
        ]
        escalation_triggers = [
            "Pasa a desacato si la segunda instancia concede y la orden sigue incumplida.",
        ]

    delivery_channels = ["panel"]
    if user_email:
        delivery_channels.append("email")
    customer_copy_channels = ["panel"]
    if user_email:
        customer_copy_channels.append("email")
    if user_phone:
        customer_copy_channels.append("whatsapp_pending")

    lowered_action = recommended_action.lower()
    radicado_destination_note = "El radicado o comprobante definitivo depende del canal usado y de la respuesta de la entidad."
    if any(token in lowered_action for token in ["tutela", "impugnacion", "desacato"]):
        radicado_destination_note = (
            "En tramites judiciales, el comprobante visible aqui corresponde al cierre registrado por la plataforma cuando existe. "
            "Las novedades del juzgado o de la EPS pueden llegar directamente al correo o al telefono informado por la persona usuaria. "
            f"Si recibes una respuesta, requerimiento o decision por fuera del panel, debes reportarla o subir la evidencia para actualizar el seguimiento. "
            f"Si una respuesta operativa llega a {settings.radications_email}, tambien la reflejaremos en el expediente."
        )
    elif "peticion" in lowered_action:
        radicado_destination_note = (
            f"En peticiones a EPS o entidades de salud, el acuse o radicado suele llegar al canal desde el que se envio o al correo informado para notificaciones, "
            f"incluido {settings.notifications_email} cuando ese sea el remitente operativo."
        )

    return {
        "mode": mode,
        "channel": channel,
        "submission_policy": submission_policy,
        "proof_type": proof_type,
        "proof_delivery_channels": submission_policy.get("customer_evidence_channels") or delivery_channels,
        "customer_copy_channels": customer_copy_channels,
        "customer_notification_channel": "email" if user_email else "panel",
        "evolution_api_role": "notificacion_al_cliente" if user_email else "pendiente",
        "whatsapp_copy_status": "pending_integration" if user_phone else "not_available",
        "operational_mailboxes": {
            "radications": settings.radications_email,
            "support": settings.support_email,
            "notifications": settings.notifications_email,
        },
        "notification_provider": settings.notification_provider,
        "mail_hosting_provider": "hostinger",
        "estimated_response_window": estimated_response_window,
        "next_step_suggestion": next_step,
        "continuity_offers": continuity,
        "follow_up_watch_items": follow_up_watch_items,
        "escalation_triggers": escalation_triggers,
        "judicial_radicado_note": radicado_destination_note,
        "post_radicado_copy": {
            "headline": "Tu tramite fue enviado y ya puedes seguirlo desde tu panel.",
            "body": (
                "Recibiras por correo una copia del documento enviado y, cuando exista, el comprobante disponible. "
                "Si el juzgado, la EPS o la entidad responde a tu correo o por llamada directa, debes reportar esa novedad para mantener actualizado el seguimiento en tu panel."
            ),
        },
        "routing_snapshot": {
            "destination_name": (routing.get("primary_target") or {}).get("name"),
            "destination_scope": routing.get("target_scope"),
            "territorial_match": routing.get("territorial_match"),
            "territorial_note": routing.get("territorial_note"),
            "destination_channel": channel,
            "radicado": radicado,
        },
    }


def build_document(case: dict[str, Any]) -> str:
    return build_document_from_template(case)

    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    target = (routing.get("primary_target") or {}).get("name") or "la autoridad competente"
    contact = (routing.get("primary_target") or {}).get("contact") or "Canal por definir"
    rights = legal_analysis.get("derechos_vulnerados") or []
    rules = legal_analysis.get("normas_relevantes") or []
    rights_text = ", ".join(rights) if isinstance(rights, list) else str(rights)
    rules_text = ", ".join(rules) if isinstance(rules, list) else str(rules)
    facts = case.get("facts") or {}
    summary = facts.get("hechos_principales") or case.get("descripcion") or ""
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Señores
{target}
Canal sugerido: {contact}

Referencia: {case.get('recommended_action')}

Yo, {case.get('usuario_nombre')}, identificado(a) con cédula {case.get('usuario_documento')}, correo {case.get('usuario_email')} y teléfono {case.get('usuario_telefono')}, residente en {case.get('usuario_direccion')}, {case.get('usuario_ciudad')}, {case.get('usuario_departamento')}, presento esta solicitud.

Hechos relevantes:
{summary}

Derechos comprometidos:
{rights_text or 'Pendientes de consolidar con el expediente.'}

Fundamento jurídico:
{rules_text or case.get('strategy_text')}

Pretensiones sugeridas:
1. Que se protejan mis derechos de forma inmediata.
2. Que se dé respuesta de fondo dentro del término legal.
3. Que se remita constancia de radicación o actuación adelantada.

Notas operativas:
{case.get('strategy_text')}

Generado por 123tutela: {generated_at}

Atentamente,
{case.get('usuario_nombre')}
CC: {case.get('usuario_documento')}
Correo: {case.get('usuario_email')}
Teléfono: {case.get('usuario_telefono')}
"""


def generate_radicado(prefix: str = "123TUT") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return f"{prefix}-{stamp}-{uuid4().hex[:6].upper()}"
