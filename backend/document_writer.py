from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.document_quality import get_generation_brief
from backend.document_rules import get_document_rule


def _join_list(value: Any, fallback: str = "No informado") -> str:
    if isinstance(value, list):
        clean = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(clean) if clean else fallback
    text = str(value or "").strip()
    return text or fallback


def _numbered_lines(items: list[str]) -> str:
    items = [str(item).strip() for item in items if str(item).strip()]
    if not items:
        return "1. Sin informacion adicional registrada."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _paragraph_lines(items: list[str], fallback: str = "Sin informacion adicional registrada.") -> str:
    items = [str(item).strip() for item in items if str(item).strip()]
    if not items:
        return fallback
    return "\n\n".join(items)


def _sentence(value: str | None, fallback: str = "No informado.") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    if text[-1] not in ".;:":
        text += "."
    return text


def _list_from_insights(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _generic_facts(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    chronology = _list_from_insights(insights.get("chronology"))
    if chronology:
        return chronology

    lines: list[str] = []
    main_facts = str(facts.get("hechos_principales") or case.get("descripcion") or "").strip()
    if main_facts:
        lines.append(_sentence(main_facts))
    entities = _join_list(facts.get("entidades_involucradas"), fallback="")
    if entities:
        lines.append(f"Se identifica como entidad o destinatario involucrado a {entities}.")
    dates = _join_list(facts.get("fechas_mencionadas"), fallback="")
    if dates:
        lines.append(f"Las referencias temporales relevantes del caso son las siguientes: {dates}.")
    central_problem = str(facts.get("problema_central") or "").strip()
    if central_problem:
        lines.append(f"El problema central del caso puede sintetizarse asi: {central_problem}.")
    return lines or ["La persona usuaria reporta una situacion que requiere documentacion juridica y seguimiento formal."]


def _generic_failures(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    failures = _list_from_insights(insights.get("entity_failures"))
    if failures:
        return failures
    return ["Se advierte una actuacion presuntamente irregular de la entidad o autoridad involucrada que exige respuesta de fondo y correccion efectiva."]


def _generic_pretensions(case: dict[str, Any], action_key: str) -> list[str]:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    pretensions = _list_from_insights(insights.get("pretensions"))
    if pretensions:
        return pretensions

    intake_form = facts.get("intake_form") or {}
    concrete_request = str(intake_form.get("concrete_request") or facts.get("pretension_concreta") or "").strip()
    if concrete_request:
        return [concrete_request, "Que la entidad emita respuesta formal y verificable frente a cada solicitud planteada."]

    description = str(case.get("descripcion") or "").lower()
    if action_key == "accion de tutela":
        return [
            "Que se amparen de manera inmediata los derechos fundamentales comprometidos.",
            "Que se ordene a la entidad accionada la actuacion concreta necesaria para cesar la vulneracion.",
        ]
    if action_key in {"derecho de peticion", "derecho de peticion financiero"}:
        return [
            "Que se emita respuesta de fondo, clara, congruente y completa frente a este escrito.",
            "Que se remita respuesta por el canal de notificacion informado por la persona usuaria.",
        ]
    if "solicito" in description or "requiero" in description:
        return ["Que se atienda de fondo la solicitud planteada por la persona usuaria."]
    return ["Que se adopte la medida correctiva o de proteccion que corresponda conforme a los hechos narrados."]


def _build_financial_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    insights = facts.get("document_insights") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}
    metadata = primary.get("metadata") or {}

    entity_name = str(intake.get("target_entity") or primary.get("name") or "Entidad financiera").strip()
    representative = str(intake.get("legal_representative") or metadata.get("legal_representative") or "").strip()
    target_line = entity_name if not representative else f"{entity_name}\nAtn. {representative}"
    contact = str(
        intake.get("target_pqrs_email")
        or intake.get("target_notification_email")
        or primary.get("contact")
        or intake.get("target_website")
        or "Canal oficial de atencion"
    ).strip()

    user_name = case.get("usuario_nombre") or "Usuario"
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    address = case.get("usuario_direccion") or "Sin direccion registrada"
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    rights_text = _join_list(legal_analysis.get("derechos_vulnerados"), fallback="proteccion del consumidor financiero y debido proceso contractual")
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    product_type = str(intake.get("bank_product_type") or "producto financiero").strip()
    subject = f"Reclamacion financiera por irregularidades relacionadas con {product_type}"
    chronology = _generic_facts(case)
    failures = _generic_failures(case)
    pretensions = _generic_pretensions(case, rule["action_key"])
    legal_basis = str(insights.get("legal_basis_summary") or "").strip() or (
        f"El presente reclamo se fundamenta en la necesidad de proteger {rights_text}."
    )
    if verified_basis:
        legal_basis = f"{legal_basis} {verified_basis}".strip()
    evidence_text = _join_list(rule.get("suggested_evidence"), fallback="extractos, capturas, contrato y comunicaciones previas")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Señores
{target_line}
Canal sugerido: {contact}

Asunto: {subject}

Yo, {user_name}, identificado(a) con cédula {user_doc}, con domicilio en {address}, {city}, {department}, correo electrónico {user_email} y teléfono {user_phone}, actuando en calidad de consumidor(a) financiero(a), presento la siguiente reclamación:

DESTINATARIO
La presente reclamación se dirige a {entity_name}, entidad que administra el producto o servicio financiero objeto de controversia.

2. Identificación del consumidor financiero
Nombre: {user_name}
Cédula: {user_doc}
Correo: {user_email}
Teléfono: {user_phone}
Dirección: {address}, {city}, {department}

HECHOS Y CONTEXTO
{_paragraph_lines(chronology)}

IRREGULARIDADES ATRIBUIDAS A LA ENTIDAD
{_paragraph_lines(failures)}

FUNDAMENTO DEL RECLAMO
{legal_basis}

SOLICITUDES
{_numbered_lines(pretensions)}

PRUEBAS Y ANEXOS
Como soportes del presente reclamo se aportan o se anuncian los siguientes elementos: {evidence_text}.

NOTIFICACIONES
Solicito que toda respuesta o decision relacionada con esta reclamación sea remitida al correo {user_email} y al teléfono {user_phone}.

Constancia de generación: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Teléfono: {user_phone}
"""


def _build_generic_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}
    user_name = case.get("usuario_nombre") or "Usuario"
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    address = case.get("usuario_direccion") or "Sin direccion registrada"
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    target = str(primary.get("name") or _join_list(facts.get("entidades_involucradas"), fallback="la autoridad o entidad competente")).strip()
    contact = str(primary.get("contact") or "Canal por definir").strip()
    chronology = _generic_facts(case)
    failures = _generic_failures(case)
    pretensions = _generic_pretensions(case, rule["action_key"])
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    legal_basis = str(insights.get("legal_basis_summary") or "").strip() or (
        f"El caso se sustenta en los siguientes derechos o intereses comprometidos: {_join_list(legal_analysis.get('derechos_vulnerados'))}."
    )
    if verified_basis:
        legal_basis = f"{legal_basis} {verified_basis}".strip()
    evidence_text = _join_list(rule.get("suggested_evidence"))
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Señores
{target}
Canal sugerido: {contact}

Referencia: {rule['document_title']}

Yo, {user_name}, identificado(a) con cédula {user_doc}, con correo {user_email}, teléfono {user_phone} y residencia en {address}, {city}, {department}, presento el siguiente escrito:

DESTINATARIO
El presente documento se dirige a {target}, como autoridad o entidad llamada a responder por los hechos aquí descritos.

HECHOS Y CRONOLOGIA
{_paragraph_lines(chronology)}

FALLAS O VULNERACIONES ATRIBUIDAS
{_paragraph_lines(failures)}

FUNDAMENTO JURIDICO
{legal_basis}

PRETENSIONES O SOLICITUDES CONCRETAS
{_numbered_lines(pretensions)}

PRUEBAS Y ANEXOS
Como soportes del presente escrito se anuncian o aportan los siguientes elementos: {evidence_text}.

NOTIFICACIONES
Solicito que toda respuesta o decision relacionada con este asunto sea comunicada al correo {user_email} y al teléfono {user_phone}.

Constancia de generación: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Teléfono: {user_phone}
"""


def build_document(case: dict[str, Any]) -> str:
    rule = get_document_rule(case.get("recommended_action"), case.get("workflow_type"))
    if rule["action_key"] in {"reclamacion financiera", "derecho de peticion financiero"}:
        return _build_financial_document(case, rule)
    return _build_generic_document(case, rule)
