from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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


def _section(title: str, body: str) -> str:
    return f"{title}\n{body.strip()}\n"


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
    chronology_text = _paragraph_lines(_generic_facts(case))
    failures_text = _paragraph_lines(_generic_failures(case))
    pretensions = _generic_pretensions(case, rule["action_key"])
    legal_basis = str(insights.get("legal_basis_summary") or "").strip() or (
        f"El presente reclamo se fundamenta en la necesidad de proteger {rights_text}."
    )
    if verified_basis:
        legal_basis = f"{legal_basis} {verified_basis}".strip()
    evidence_text = _join_list(rule.get("suggested_evidence"), fallback="extractos, capturas, contrato y comunicaciones previas")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    consumer_profile = (
        f"Nombre: {user_name}\n"
        f"Documento: {user_doc}\n"
        f"Correo: {user_email}\n"
        f"Telefono: {user_phone}\n"
        f"Direccion: {address}, {city}, {department}"
    )

    return f"""Senores
{target_line}
Canal sugerido: {contact}

Asunto: {subject}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con domicilio en {address}, {city}, {department}, correo electronico {user_email} y telefono {user_phone}, actuando en calidad de consumidor(a) financiero(a), presento la siguiente reclamacion formal.

{_section("DESTINATARIO", f"La presente reclamacion se dirige a {entity_name}, entidad que administra el producto o servicio financiero objeto de controversia y que debe emitir respuesta integral, motivada y verificable frente a los hechos aqui expuestos.")}
{_section("IDENTIFICACION DEL CONSUMIDOR FINANCIERO", consumer_profile)}
{_section("HECHOS Y CONTEXTO", chronology_text)}
{_section("IRREGULARIDADES ATRIBUIDAS A LA ENTIDAD", failures_text)}
{_section("FUNDAMENTO DEL RECLAMO", legal_basis)}
{_section("SOLICITUDES", _numbered_lines(pretensions))}
{_section("PRUEBAS Y ANEXOS", f"Como soportes del presente reclamo se aportan o se anuncian los siguientes elementos: {evidence_text}.")}
{_section("NOTIFICACIONES", f"Solicito que toda respuesta o decision relacionada con esta reclamacion sea remitida al correo {user_email} y al telefono {user_phone}.")}
Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
"""


def _build_petition_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}

    target = str(intake.get("target_entity") or primary.get("name") or _join_list(facts.get("entidades_involucradas"), fallback="Entidad destinataria")).strip()
    contact = str(primary.get("contact") or intake.get("target_pqrs_email") or intake.get("target_website") or "Canal oficial de atencion").strip()
    user_name = case.get("usuario_nombre") or "Usuario"
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    address = case.get("usuario_direccion") or "Sin direccion registrada"
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    chronology_text = _paragraph_lines(_generic_facts(case))
    pretensions = _generic_pretensions(case, rule["action_key"])
    evidence_text = _join_list(rule.get("suggested_evidence"), fallback="documentos soporte del caso")
    request_type = str(intake.get("request_type") or "interes particular").replace("_", " ").strip()
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Senores
{target}
Canal sugerido: {contact}

Asunto: Derecho de peticion de {request_type}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con domicilio en {address}, {city}, {department}, correo electronico {user_email} y telefono {user_phone}, en ejercicio del derecho fundamental de peticion consagrado en el articulo 23 de la Constitucion Politica y desarrollado por la Ley 1755 de 2015, presento la siguiente solicitud.

{_section("IDENTIFICACION DEL PETICIONARIO", f"Nombre: {user_name}\nCedula: {user_doc}\nCorreo: {user_email}\nTelefono: {user_phone}\nDireccion: {address}, {city}, {department}")}
{_section("HECHOS Y CONTEXTO", chronology_text)}
{_section("FUNDAMENTO DEL DERECHO DE PETICION", f"La presente peticion se formula para obtener una respuesta de fondo, clara, congruente y completa sobre los hechos y solicitudes aqui expuestos. {verified_basis}".strip())}
{_section("SOLICITUDES NUMERADAS", _numbered_lines(pretensions))}
{_section("TERMINO DE RESPUESTA", "Solicito respuesta de fondo dentro de los terminos legales aplicables conforme a la Ley 1755 de 2015.")}
{_section("ANEXOS Y NOTIFICACIONES", f"Como soporte de esta peticion se anuncian o se aportan los siguientes elementos: {evidence_text}.")}
{_section("NOTIFICACIONES", f"Solicito que la respuesta sea enviada al correo {user_email} y al telefono {user_phone}.")}
Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
"""


def _build_tutela_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    insights = facts.get("document_insights") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}

    accionado = str(intake.get("target_entity") or primary.get("name") or _join_list(facts.get("entidades_involucradas"), fallback="Entidad accionada")).strip()
    user_name = case.get("usuario_nombre") or "Usuario"
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    address = case.get("usuario_direccion") or "Sin direccion registrada"
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    rights = _join_list(legal_analysis.get("derechos_vulnerados"), fallback="derechos fundamentales comprometidos")
    chronology_text = _paragraph_lines(_generic_facts(case))
    pretensions = _generic_pretensions(case, rule["action_key"])
    evidence_text = _join_list(rule.get("suggested_evidence"), fallback="documentos soporte del caso")
    procedencia = facts.get("tutela_procedencia") or {}
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    subsidiarity = _sentence(
        intake.get("tutela_other_means_detail")
        or (
            "La accion de tutela resulta necesaria por cuanto no existe otro medio judicial eficaz o, de existir, no ofrece proteccion oportuna frente al dano actual."
            if procedencia.get("subscores", {}).get("subsidiariedad") in {"alta", "media"}
            else ""
        ),
        "La accion se presenta como mecanismo de proteccion inmediata dada la insuficiencia de otros medios eficaces frente a la situacion actual.",
    )
    immediacy = _sentence(
        intake.get("tutela_immediacy_detail")
        or "La vulneracion se mantiene actual o reciente, por lo que la solicitud cumple el requisito de inmediatez.",
        "La vulneracion se mantiene actual o reciente, por lo que la solicitud cumple el requisito de inmediatez.",
    )
    no_temerity = _sentence(
        intake.get("tutela_no_temperity_detail")
        or "Bajo la gravedad del juramento manifiesto que no he presentado otra accion de tutela por los mismos hechos, derechos y pretensiones, salvo lo que se informe expresamente en este escrito.",
        "Bajo la gravedad del juramento manifiesto que no he presentado otra accion de tutela por los mismos hechos, derechos y pretensiones.",
    )
    legal_basis_text = f"{str(insights.get('legal_basis_summary') or '').strip() or 'La situacion descrita compromete derechos fundamentales y requiere proteccion judicial inmediata.'} {verified_basis}".strip()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Senor Juez Constitucional (Reparto)
{city}, {department}

Referencia: Accion de tutela para la proteccion de {rights}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con domicilio en {address}, {city}, {department}, correo electronico {user_email} y telefono {user_phone}, actuando en nombre propio, presento accion de tutela contra {accionado}, con fundamento en el articulo 86 de la Constitucion Politica y el Decreto 2591 de 1991.

{_section("COMPETENCIA Y REPARTO", "Por la naturaleza de los hechos y la necesidad de proteccion inmediata de derechos fundamentales, solicito el reparto de esta accion de tutela al despacho competente.")}
{_section("ACCIONADO", f"La presente solicitud se dirige contra {accionado}, por los hechos y omisiones que se exponen a continuacion.")}
{_section("HECHOS CRONOLOGICOS", chronology_text)}
{_section("DERECHOS FUNDAMENTALES VULNERADOS", f"Conforme a los hechos narrados, considero comprometidos los siguientes derechos fundamentales: {rights}.")}
{_section("FUNDAMENTO JURIDICO", legal_basis_text)}
{_section("PROCEDENCIA", f"Subsidiariedad: {subsidiarity}\n\nInmediatez: {immediacy}")}
{_section("PRETENSIONES", _numbered_lines(pretensions))}
{_section("PRUEBAS Y ANEXOS", f"Como soporte de la presente accion se anuncian o se aportan los siguientes elementos: {evidence_text}.")}
{_section("JURAMENTO DE NO TEMERIDAD", no_temerity)}
{_section("NOTIFICACIONES", f"Solicito que las notificaciones del presente tramite sean remitidas al correo {user_email} y al telefono {user_phone}.")}
Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
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
    chronology_text = _paragraph_lines(_generic_facts(case))
    failures_text = _paragraph_lines(_generic_failures(case))
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

    return f"""Senores
{target}
Canal sugerido: {contact}

Referencia: {rule['document_title']}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con correo {user_email}, telefono {user_phone} y residencia en {address}, {city}, {department}, presento el siguiente escrito formal.

{_section("DESTINATARIO", f"El presente documento se dirige a {target}, como autoridad o entidad llamada a responder por los hechos aqui descritos.")}
{_section("HECHOS Y CRONOLOGIA", chronology_text)}
{_section("FALLAS O VULNERACIONES ATRIBUIDAS", failures_text)}
{_section("FUNDAMENTO JURIDICO", legal_basis)}
{_section("PRETENSIONES O SOLICITUDES CONCRETAS", _numbered_lines(pretensions))}
{_section("PRUEBAS Y ANEXOS", f"Como soportes del presente escrito se anuncian o aportan los siguientes elementos: {evidence_text}.")}
{_section("NOTIFICACIONES", f"Solicito que toda respuesta o decision relacionada con este asunto sea comunicada al correo {user_email} y al telefono {user_phone}.")}
Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
"""


def build_document(case: dict[str, Any]) -> str:
    rule = get_document_rule(case.get("recommended_action"), case.get("workflow_type"))
    if rule["action_key"] == "accion de tutela":
        return _build_tutela_document(case, rule)
    if rule["action_key"] in {"reclamacion financiera", "derecho de peticion financiero"}:
        return _build_financial_document(case, rule)
    if "derecho de peticion" in rule["action_key"]:
        return _build_petition_document(case, rule)
    return _build_generic_document(case, rule)
