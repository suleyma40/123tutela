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
    if not items:
        return "1. Sin informacion adicional registrada."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _sentence(value: str | None, fallback: str = "No informado.") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    return text if text.endswith((".", ":", ";")) else f"{text}."


def _facts_lines(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts") or {}
    lines: list[str] = []

    main_facts = str(facts.get("hechos_principales") or case.get("descripcion") or "").strip()
    if main_facts:
        lines.append(main_facts)

    entities = _join_list(facts.get("entidades_involucradas"), fallback="")
    if entities:
        lines.append(f"Entidad o destinatario involucrado: {entities}.")

    dates = _join_list(facts.get("fechas_mencionadas"), fallback="")
    if dates:
        lines.append(f"Fechas o referencias temporales relevantes: {dates}.")

    central_problem = str(facts.get("problema_central") or "").strip()
    if central_problem:
        lines.append(f"Problema central identificado: {central_problem}.")

    return lines or ["El usuario reporta una situacion que requiere documentacion juridica y seguimiento formal."]


def _list_from_insights(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _pretension_lines(case: dict[str, Any], action_key: str) -> list[str]:
    facts = case.get("facts") or {}
    intake_form = facts.get("intake_form") or {}
    concrete_request = str(intake_form.get("concrete_request") or facts.get("pretension_concreta") or "").strip()
    if concrete_request:
        return [
            concrete_request,
            "Dar respuesta formal y oportuna a cada solicitud presentada por la persona usuaria.",
        ]

    description = str(case.get("descripcion") or "")
    lowered = description.lower()

    if action_key == "accion de tutela":
        return [
            "Amparar de manera inmediata los derechos fundamentales identificados en este escrito.",
            "Ordenar a la entidad accionada la actuacion concreta que supere la vulneracion reportada.",
            "Notificar al accionante la decision y su cumplimiento por el canal indicado.",
        ]
    if action_key == "derecho de peticion":
        return [
            "Dar respuesta de fondo, clara y completa a cada solicitud formulada.",
            "Entregar la informacion, documento o certificacion requerida, si aplica.",
            "Remitir la respuesta al canal de notificacion indicado por el peticionario.",
        ]
    if action_key == "queja formal":
        return [
            "Registrar formalmente la queja y trasladarla al area competente.",
            "Informar las actuaciones de verificacion o correccion que correspondan.",
            "Remitir respuesta formal al usuario.",
        ]
    if action_key == "reclamo administrativo":
        return [
            "Revisar de fondo la actuacion, cobro o decision cuestionada.",
            "Corregir el error identificado o motivar de manera suficiente la negativa.",
            "Informar por escrito la solucion adoptada y su soporte.",
        ]
    if action_key == "queja disciplinaria":
        return [
            "Admitir la queja y valorar la apertura de indagacion o investigacion disciplinaria.",
            "Practicar las actuaciones iniciales necesarias para verificar los hechos denunciados.",
            "Informar al quejoso el tramite dado a la denuncia.",
        ]
    if action_key == "accion de cumplimiento":
        return [
            "Ordenar a la autoridad accionada cumplir la norma o acto administrativo identificado.",
            "Fijar el plazo razonable para su cumplimiento efectivo.",
            "Disponer las comunicaciones necesarias al accionante.",
        ]
    if action_key == "impugnacion de tutela":
        return [
            "Revocar o modificar el fallo de primera instancia en lo que resulte desfavorable al accionante.",
            "Conceder la proteccion integral del derecho fundamental comprometido.",
            "Valorar las pruebas y argumentos que no fueron apreciados de manera suficiente.",
        ]
    if action_key == "incidente de desacato":
        return [
            "Declarar el incumplimiento de la orden de tutela si se encuentra probado.",
            "Ordenar el cumplimiento inmediato del fallo.",
            "Adoptar las medidas sancionatorias o correctivas a que haya lugar.",
        ]

    if "solicito" in lowered or "pido" in lowered or "requiero" in lowered:
        return [
            "Atender de fondo la solicitud planteada por el usuario.",
            "Dar respuesta formal y oportuna por el canal indicado.",
        ]

    return [
        "Atender de fondo la solicitud planteada por el usuario.",
        "Adoptar la medida que corresponda segun los hechos y soportes aportados.",
    ]


def _build_financial_claim_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
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
    rights_text = _join_list(legal_analysis.get("derechos_vulnerados"), fallback="Debido proceso, informacion clara y proteccion del consumidor financiero")
    rules_text = _join_list(
        legal_analysis.get("normas_relevantes"),
        fallback="Ley 1328 de 2009, Estatuto del Consumidor y reglas de proteccion al consumidor financiero",
    )
    product_type = str(intake.get("bank_product_type") or "tarjeta de credito").strip()
    disputed_charge = str(intake.get("disputed_charge") or "seguro no autorizado").strip()
    case_story = _sentence(intake.get("case_story") or facts.get("hechos_principales"))
    dates = _sentence(intake.get("key_dates") or facts.get("fechas_mencionadas"), fallback="No fue posible consolidar fechas exactas; el cargo es reciente y actualmente sigue afectando a la usuaria.")
    request = _sentence(intake.get("concrete_request") or facts.get("pretension_concreta"))
    prior_claim = (
        _sentence(intake.get("prior_claim_result"))
        if str(intake.get("prior_claim") or "").strip() == "si"
        else "A la fecha de este escrito no he recibido solucion efectiva frente a la situacion reportada."
    )
    evidence_text = _join_list(rule.get("suggested_evidence"), fallback="Extractos, capturas, contrato y comunicaciones previas")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Señores
{target_line}
Canal sugerido: {contact}

Asunto: Reclamación financiera por cobro no autorizado en {product_type}

Yo, {user_name}, identificado(a) con cédula {user_doc}, con domicilio en {address}, {city}, {department}, correo electrónico {user_email} y teléfono {user_phone}, actuando en calidad de consumidor(a) financiero(a), presento la siguiente reclamación:

1. Destinatario
La presente reclamación se dirige a {entity_name}, en su calidad de entidad financiera responsable del producto y de los cobros aquí cuestionados.

2. Identificación del consumidor financiero
Nombre: {user_name}
Cédula: {user_doc}
Correo: {user_email}
Teléfono: {user_phone}
Dirección: {address}, {city}, {department}

3. Hechos y contexto
1. Soy titular o usuario(a) del producto financiero {product_type} ofrecido o administrado por {entity_name}.
2. He advertido el cobro de {disputed_charge}, situación que no reconozco como autorizada, aceptada ni informada de manera suficiente.
3. Relato del caso: {case_story}
4. Fechas o referencias temporales relevantes: {dates}
5. Gestión previa y respuesta recibida: {prior_claim}

4. Fundamento del reclamo
Esta reclamación se presenta con fundamento en los derechos del consumidor financiero a recibir información clara, suficiente y verificable, a no asumir cobros no autorizados y a obtener una respuesta completa y de fondo frente a sus reclamaciones. Como soporte jurídico base invoco: {rules_text}. Derechos o intereses comprometidos: {rights_text}.

5. Solicitudes numeradas
1. {request}
2. Que se me informe de manera clara el origen del cobro cuestionado, la supuesta autorización que lo respaldaría y la fecha exacta en que fue incorporado al producto.
3. Que, si la entidad no acredita autorización válida, se elimine de inmediato el cobro cuestionado y se reversen o devuelvan los valores cobrados indebidamente.
4. Que se remita respuesta escrita, completa y de fondo al correo {user_email}.

6. Pruebas y anexos
Como soportes del presente reclamo aportaré o aportaré oportunamente: {evidence_text}.

7. Notificaciones
Autorizo recibir respuesta y cualquier comunicación relacionada con esta reclamación en el correo {user_email} y en el teléfono {user_phone}.

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
        return _build_financial_claim_document(case, rule)

    brief = get_generation_brief(case.get("recommended_action"), case.get("workflow_type"))
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    target = (routing.get("primary_target") or {}).get("name") or "la autoridad competente"
    contact = (routing.get("primary_target") or {}).get("contact") or "Canal por definir"
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    user_name = case.get("usuario_nombre") or "Usuario"
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    address = case.get("usuario_direccion") or ""
    rights_text = _join_list(legal_analysis.get("derechos_vulnerados"))
    rules_text = _join_list(legal_analysis.get("normas_relevantes"))
    evidence_text = _join_list(rule.get("suggested_evidence"))
    facts_text = _numbered_lines(_facts_lines(case))
    pretensions_text = _numbered_lines(_pretension_lines(case, rule["action_key"]))
    quality_focus = rule.get("quality_focus") or "claridad, precision y peticiones ejecutables"
    focus_text = _numbered_lines([str(item) for item in brief.get("narrative_focus", [])])
    must_include_text = _numbered_lines([str(item) for item in brief.get("must_include", [])])
    section_text = _numbered_lines([str(item) for item in brief.get("required_sections", [])])
    tone_text = brief.get("tone") or "claro, serio y accionable"

    return f"""Senores
{target}
Canal sugerido: {contact}

Referencia: {rule['document_title']}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con correo {user_email}, telefono {user_phone} y residencia en {address}, {city}, {department}, presento el siguiente escrito.

1. Objeto del documento
{rule['goal']}

2. Hechos relevantes
{facts_text}

3. Derechos, interes juridico o fundamento principal
Derechos o intereses comprometidos: {rights_text}.
Soporte normativo principal: {rules_text}.

4. Pretensiones o solicitudes concretas
{pretensions_text}

5. Pruebas y anexos sugeridos
{evidence_text}.

6. Tecnica narrativa y juridica exigida
Tono exigido: {tone_text}.
Enfoques que debe sostener el escrito:
{focus_text}

7. Controles minimos antes de entregar
{must_include_text}

8. Estructura obligatoria del documento final
{section_text}

9. Enfoque de calidad exigido para este documento
{quality_focus}.

10. Notificaciones
Solicito que cualquier respuesta o decision sea comunicada al correo {user_email} y al telefono {user_phone}.

Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
"""
