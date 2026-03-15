from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from backend import repository_ext as repository


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
        if all_required_done or urgent:
            workflow_type = "tutela"
            recommended_action = "Accion de tutela"
        else:
            workflow_type = "derecho_peticion"
            recommended_action = "Derecho de peticion a EPS"
            warnings.append("Antes de tutela en salud, la via previa ante EPS debe quedar documentada salvo urgencia manifiesta.")
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

    targets: list[dict[str, Any]] = []
    if workflow_type == "tutela":
        targets.extend(_build_target_from_court(item) for item in repository.search_court_targets(city, department))
    else:
        targets.extend(_build_target_from_entity(item) for item in repository.search_entities(category, entity_names))

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


def build_document(case: dict[str, Any]) -> str:
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
