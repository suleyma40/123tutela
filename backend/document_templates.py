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


def build_document(case: dict[str, Any]) -> str:
    rule = get_document_rule(case.get("recommended_action"), case.get("workflow_type"))
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
