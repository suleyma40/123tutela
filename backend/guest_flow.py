from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from backend.config import settings


BASE_SERVICE_PRICE_COP = 49_900
SERVICE_PRODUCT_CODE = "hazlopormi_v1"
SERVICE_PRODUCT_NAME = "HazloPorMi 24h"

_CATEGORY_ALIASES = {
    "salud": "Salud",
    "eps": "Salud",
    "transito": "Tránsito",
    "tránsito": "Tránsito",
    "bancos": "Bancos",
    "banco": "Bancos",
}


def normalize_guest_category(value: str) -> str:
    lowered = str(value or "").strip().lower()
    return _CATEGORY_ALIASES.get(lowered, str(value or "").strip().title() or "Salud")


def build_public_token() -> str:
    return uuid4().hex + uuid4().hex[:8]


def compute_sla_deadline(started_at: datetime | None = None) -> datetime:
    base = (started_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    deadline = base + timedelta(days=1)
    while deadline.weekday() >= 5:
        deadline += timedelta(days=1)
    return deadline


def _text(value: Any) -> str:
    return str(value or "").strip()


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return cleaned.strip("-") or "documento"


def build_customer_summary(case: dict[str, Any]) -> dict[str, Any]:
    action = _text(case.get("recommended_action")) or "Documento recomendado"
    category = _text(case.get("categoria") or case.get("category")) or "Caso"
    return {
        "headline": f"Detectamos un caso de {category.lower()} con accion sugerida: {action}.",
        "subheadline": "Si completas el pago y la informacion requerida, el equipo entregara documento y guia detallada en hasta 24 horas habiles.",
        "included": [
            "Diagnostico inicial del caso",
            "Redaccion humana del documento final",
            "Checklist de anexos y pasos concretos",
            "Entrega por email y WhatsApp",
        ],
        "time_promise": "Hasta 24 horas habiles desde pago aprobado e informacion completa.",
    }


def _guide_template(
    *,
    title: str,
    where: str,
    how: str,
    attachments: list[str],
    asks: list[str],
    expected_window: str,
    no_response: str,
    denied: str,
) -> dict[str, Any]:
    return {
        "title": title,
        "what_you_will_present": title,
        "where_to_submit": where,
        "how_to_submit": how,
        "required_attachments": attachments,
        "what_to_ask_for": asks,
        "how_to_keep_proof": "Guarda captura del radicado, correo enviado, sello de recibido o comprobante del portal.",
        "estimated_response_window": expected_window,
        "next_step_if_no_response": no_response,
        "next_step_if_denied": denied,
    }


def build_customer_guide(case: dict[str, Any]) -> dict[str, Any]:
    category = normalize_guest_category(_text(case.get("categoria") or case.get("category")))
    action = _text(case.get("recommended_action")).lower()
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}

    if category == "Salud" and "tutela" in action:
        return _guide_template(
            title="Accion de tutela en salud",
            where="Juzgado competente, ventanilla judicial, correo oficial o portal habilitado segun tu ciudad.",
            how="Presenta el PDF firmado con tus anexos medicos. Si la tutela es urgente, prioriza canal judicial que genere constancia o radicado.",
            attachments=[
                "Cedula",
                "Orden medica o formula",
                "Historia clinica o soporte reciente",
                "Prueba de negativa, demora o falta de entrega",
                "Prueba de gestion previa si existe",
            ],
            asks=[
                "Autorizar, entregar o programar el servicio de salud solicitado",
                "Responder de fondo y sin barreras administrativas",
                "Adoptar medida urgente si el riesgo sigue ocurriendo hoy",
            ],
            expected_window="Las actuaciones judiciales suelen moverse en horas o pocos dias, no en el plazo ordinario de peticiones.",
            no_response="Si el juzgado requiere algo adicional, responde de inmediato y conserva el numero de radicado.",
            denied="Si la decision niega o limita la solicitud, revisa si procede impugnacion dentro del termino judicial aplicable.",
        )
    if category == "Salud":
        return _guide_template(
            title="Derecho de peticion o queja en salud",
            where="EPS, IPS, portal PQRS, correo oficial o punto fisico de atencion.",
            how="Radica el documento con todos los soportes medicos y pide constancia de recibido o numero de radicado.",
            attachments=[
                "Cedula",
                "Orden medica o formula",
                "Historia clinica o resumen medico",
                "Respuesta previa de EPS o IPS si existe",
            ],
            asks=[
                "Autorizar o entregar el servicio, medicamento o cita",
                "Indicar fecha real de cumplimiento",
                "Responder por escrito de fondo",
            ],
            expected_window="En peticiones ordinarias la entidad suele responder hasta en 15 dias habiles, salvo regla especial.",
            no_response="Si no responden de fondo o el dano sigue, evalua escalar a tutela en salud.",
            denied="Si niegan por razones administrativas o economicas, guarda la respuesta y prepara la escalada.",
        )
    if category == "Tránsito":
        return _guide_template(
            title="Derecho de peticion o recurso de transito",
            where="Secretaria de Movilidad, organismo de transito, SIMIT o dependencia de cobro competente.",
            how="Presenta el documento por ventanilla, correo oficial o portal. Si buscas desembargo o prescripcion, adjunta pruebas completas del expediente.",
            attachments=[
                "Cedula",
                "Estado de cuenta o consulta SIMIT",
                "Acto, comparendo o referencia del embargo si existe",
                "Recibo de pago o soporte de desembargo si aplica",
            ],
            asks=[
                "Corregir, levantar o revisar la actuacion de transito",
                "Certificar el estado real de la obligacion",
                "Resolver de fondo prescripcion, desembargo o recurso",
            ],
            expected_window="La respuesta depende del organismo, pero conviene hacer seguimiento con el numero de radicado desde el primer dia.",
            no_response="Si no contestan, guarda la constancia y considera insistencia formal o accion posterior segun el caso.",
            denied="Si rechazan la solicitud, revisa el fundamento y conserva recibos, actos y trazabilidad completa.",
        )
    return _guide_template(
        title="Reclamo o habeas data financiero",
        where="Banco, defensor del consumidor financiero, canal PQRS o correo oficial de la entidad.",
        how="Presenta el documento con extractos, certificaciones y soportes del cobro o reporte negativo. Pide radicado y conserva la respuesta.",
        attachments=[
            "Cedula",
            "Extractos o soporte del cobro",
            "Comunicaciones previas con el banco",
            "Prueba del reporte negativo o bloqueo",
        ],
        asks=[
            "Corregir el cobro, bloqueo o reporte",
            "Responder de fondo con soporte verificable",
            "Eliminar o rectificar el dato si no corresponde",
        ],
        expected_window="La entidad debe responder por su canal formal; el tiempo exacto depende del tipo de solicitud y del sector financiero.",
        no_response="Si no responden o la afectacion continua, conserva el radicado y prepara la escalada siguiente.",
        denied="Si rechazan el reclamo, revisa si procede nueva reclamacion, SIC o tutela segun la afectacion.",
    )


def build_operational_brief(case: dict[str, Any]) -> dict[str, Any]:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    guide = build_customer_guide(case)
    agent_state = facts.get("agent_state") or {}
    uploaded_files = list(facts.get("uploaded_evidence_files") or [])
    attachment_names = [
        _text(item.get("original_name") or item.get("name"))
        for item in uploaded_files
        if isinstance(item, dict) and _text(item.get("original_name") or item.get("name"))
    ]
    if not attachment_names:
        attachment_names = list(((facts.get("attachment_intelligence") or {}).get("evidence_names") or []))
    ops_prompts = [item for item in (agent_state.get("ops_follow_up_prompts") or []) if isinstance(item, dict)]
    urgency_label = _text(intake.get("urgency_level") or intake.get("urgency") or facts.get("problema_central"))
    return {
        "summary": _text(case.get("description") or case.get("descripcion")),
        "document_type": _text(case.get("recommended_action")),
        "category": normalize_guest_category(_text(case.get("categoria") or case.get("category"))),
        "urgency": urgency_label or "Revisar urgencia con el relato y anexos",
        "target_entity": _text(intake.get("target_entity") or intake.get("entity_name")),
        "missing_items": list((facts.get("pending_questions") or []))[:6],
        "ops_ready": bool(agent_state.get("ops_ready")),
        "ops_summary": _text(agent_state.get("ops_summary")),
        "ops_follow_up_prompts": ops_prompts,
        "ops_missing_reasons": [str(item.get("why") or item.get("question") or "").strip() for item in ops_prompts if str(item.get("why") or item.get("question") or "").strip()],
        "required_attachments": guide.get("required_attachments") or [],
        "uploaded_files": attachment_names,
        "documents_to_request_from_client": [
            attachment
            for attachment in (guide.get("required_attachments") or [])
            if attachment not in attachment_names
        ],
        "intake_snapshot": {
            "document_number": _text(intake.get("document_number")),
            "city": _text(intake.get("city")),
            "address": _text(intake.get("address")),
            "diagnosis": _text(intake.get("diagnosis")),
            "treatment_needed": _text(intake.get("treatment_needed")),
            "concrete_request": _text(intake.get("concrete_request")),
            "key_dates": _text(intake.get("key_dates")),
            "case_story": _text(intake.get("case_story")),
            "prior_claim_result": _text(intake.get("prior_claim_result") or intake.get("eps_response_detail")),
            "ongoing_harm": _text(intake.get("ongoing_harm") or intake.get("urgency_detail")),
        },
        "drafting_notes": [
            "Usar el diagnostico automatico solo como base; validar hechos y solicitud concreta.",
            "Alinear narrativa, pruebas y pretensiones con la accion sugerida.",
            "Entregar documento y checklist final al cliente en tono claro y operativo.",
        ],
    }


def build_delivery_package(case: dict[str, Any], document_relative_path: str | None = None) -> dict[str, Any]:
    guide = build_customer_guide(case)
    return {
        "document_pdf_url": f"/public/files/{document_relative_path}" if document_relative_path else None,
        "customer_guide": guide,
        "required_attachments": guide.get("required_attachments") or [],
        "submission_channel": guide.get("where_to_submit") or "",
        "estimated_response_window": guide.get("estimated_response_window") or "",
        "next_step_if_denied": guide.get("next_step_if_denied") or "",
        "next_step_if_no_response": guide.get("next_step_if_no_response") or "",
    }


def build_ops_sync_payload(case: dict[str, Any]) -> dict[str, Any]:
    summary = case.get("submission_summary") or {}
    brief = summary.get("operational_brief") or build_operational_brief(case)
    guide = summary.get("customer_guide") or build_customer_guide(case)
    return {
        "case_id": str(case.get("id") or ""),
        "public_token": summary.get("public_token") or case.get("public_token"),
        "paid_at": summary.get("payment_summary", {}).get("approved_at"),
        "sla_deadline_at": summary.get("sla_deadline_at"),
        "customer_case_code": (summary.get("customer_case") or {}).get("code"),
        "name": case.get("usuario_nombre"),
        "phone": case.get("usuario_telefono"),
        "email": case.get("usuario_email"),
        "category": case.get("categoria"),
        "recommended_action": case.get("recommended_action"),
        "urgency": brief.get("urgency"),
        "status": case.get("estado"),
        "invoice_number": (summary.get("invoice") or {}).get("number"),
        "raffle_code": (summary.get("raffle") or {}).get("code"),
        "ops_ready": brief.get("ops_ready"),
        "ops_missing_reasons": brief.get("ops_missing_reasons") or [],
        "uploaded_files": brief.get("uploaded_files") or [],
        "operational_brief": brief,
        "customer_guide": guide,
        "payment_reference": case.get("payment_reference"),
    }


def sync_case_to_ops(case: dict[str, Any]) -> dict[str, Any]:
    if not settings.n8n_ops_webhook_url:
        return {"status": "skipped", "reason": "missing_webhook"}
    payload = build_ops_sync_payload(case)
    request = urllib.request.Request(
        settings.n8n_ops_webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # nosec - url comes from env
            body = response.read().decode("utf-8", errors="ignore")
            return {"status": "sent", "code": response.status, "body": body[:500]}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        return {"status": "error", "code": exc.code, "body": detail[:500]}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def build_pdf_filename(case: dict[str, Any], title: str) -> str:
    case_id = str(case.get("id") or "")[:8]
    return f"{_slug(title)}-{case_id}.pdf"
