from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import re
from pathlib import Path
from typing import Any
import time

from fastapi import Cookie, Depends, FastAPI, File, Form, Header, HTTPException, Request, Response, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from backend.catalog_runtime import get_product, list_catalog, suggest_product_code
from backend.case_architecture import (
    build_dx_result,
    build_final_validation,
    build_layer_outputs,
    build_source_validation_policy,
    collect_pending_questions,
    evaluate_tutela_procedencia,
)
from backend.agent_orchestrator import build_health_agent_state, relax_health_tutela_blockers
from backend.config import settings
from backend.document_quality import evaluate_generated_document
from backend.document_writer import build_document_with_trace
from backend.entity_directory import search_entity_directory
from backend.document_rules_v2 import evaluate_document_rule
from backend.intake_validation_v2 import validate_intake, validate_submission_readiness
from backend.legal_service import LegalAnalyzer
from backend.legal_sources import (
    build_verified_legal_basis_text,
    resolve_verified_legal_support,
    sanitize_legal_analysis,
)
from backend.notifications import send_post_radicado_email
from backend.notifications import send_post_radicado_whatsapp
from backend.notifications import send_signed_submission_email
from backend.notifications import send_guest_delivery_email
from backend.notifications import send_guest_delivery_whatsapp
from backend.notifications import send_diagnosis_abandonment_whatsapp
from backend.submission_artifacts import create_signed_submission_artifacts
from backend.schemas_v2 import (
    AnalysisPreviewRequest,
    AnalysisPreviewResponse,
    AuthResponse,
    CatalogProductResponse,
    EntityAutocompleteResponse,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseDocumentResponse,
    DocumentGenerateRequest,
    CaseIntakeUpdateRequest,
    CaseResponse,
    CaseSubmitRequest,
    InternalStatusUpdateRequest,
    LoginRequest,
    ManualRadicadoRequest,
    FollowUpReportRequest,
    PaymentOrderResponse,
    PaymentConfirmationRequest,
    GuestCaseStatusResponse,
    GuestCheckoutSessionRequest,
    GuestCheckoutSessionResponse,
    GuestDeliveryRequest,
    GuestDiagnosisResponse,
    GuestIntakeUpdateRequest,
    GuestLeadCreateRequest,
    GuestPaymentReconcileRequest,
    RegisterRequest,
    TwoFactorDisableRequest,
    TwoFactorEnableRequest,
    TwoFactorEnableResponse,
    TwoFactorSetupResponse,
    UploadedFileResponse,
    UserProfileUpdateRequest,
    UserResponse,
    WompiCheckoutSessionRequest,
    WompiCheckoutSessionResponse,
    WompiReconcileRequest,
    WompiWebhookResponse,
)
from backend.security import create_token, decode_token, hash_password, verify_password
from backend.totp import build_otpauth_uri, generate_recovery_codes, generate_totp_secret, hash_recovery_code, verify_totp_code
from backend.storage import absolute_path, move_relative_path, save_upload
from backend.storage import ensure_upload_root
from backend.attachment_intelligence import (
    build_attachment_context,
    enrich_description_with_attachment_context,
    suggest_fields_from_context,
)
from backend import repository_ext as repository
from backend.wompi import (
    amount_cop_to_cents,
    build_checkout_payload,
    build_reference,
    ensure_checkout_configured,
    ensure_webhook_configured,
    extract_transaction_from_event,
    fetch_transaction,
    parse_approved_at,
    verify_event_signature,
)
from backend.workflows import (
    build_submission_guidance,
    build_routing,
    build_strategy_text,
    generate_radicado,
    get_submission_policy,
    infer_workflow,
    user_profile_complete,
)
from backend.guest_flow import (
    BASE_SERVICE_PRICE_COP,
    SERVICE_PRODUCT_CODE,
    SERVICE_PRODUCT_NAME,
    build_customer_guide,
    build_customer_summary,
    build_delivery_package,
    build_operational_brief,
    build_pdf_filename,
    build_public_token,
    compute_sla_deadline,
    normalize_guest_category,
    sync_case_to_ops,
)
from backend.simple_pdf import render_text_pdf


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"https?://([A-Za-z0-9-]+\.)?(hazlopormi\.app|123tutelaapp\.com)$|https?://localhost(:\d+)?$|https?://127\.0\.0\.1(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

analyzer = LegalAnalyzer(settings.knowledge_base_json)
_FAILED_LOGIN_ATTEMPTS: dict[str, list[float]] = {}
_LOGIN_LIMIT_WINDOW_SECONDS = 15 * 60
_LOGIN_MAX_ATTEMPTS = 8

SIMPLE_SIGNATURE_CONSENT_VERSION = "ses_v1"
SIMPLE_SIGNATURE_CONSENT_TEXT = (
    "Autorizo a HazloPorMi para usar mi firma electronica simple en la radicacion o envio del documento generado para este caso. "
    "Confirmo que revise el contenido final antes de aceptarlo, que los datos de identificacion y ciudad que suministro son correctos, "
    "y que esta aceptacion expresa representa mi voluntad de presentar este documento por medios electronicos en el canal aplicable. "
    "Entiendo que la plataforma conservara evidencia basica de esta aceptacion, incluida la fecha y hora, la version del consentimiento "
    "y metadatos tecnicos del envio disponibles en el sistema."
)

ADDON_PRICES_COP = {
    "filing_bundle": 36_000,
    "filing_auto": 34_000,
    "filing_guide": 17_000,
    "follow_up": 17_000,
}

ADDON_ORDER_CONFIG = {
    "filing_bundle": {
        "code": "addon_filing_bundle",
        "name": "Radicación y seguimiento",
        "description": "Paquete de radicación por HazloPorMi y seguimiento posterior del expediente.",
    },
    "filing_auto": {
        "code": "addon_filing_auto",
        "name": "Radicacion por HazloPorMi",
        "description": "Gestion de radicacion por parte de HazloPorMi cuando el canal lo permita.",
    },
    "filing_guide": {
        "code": "addon_filing_guide",
        "name": "Guia de radicacion",
        "description": "Entrega de guia operativa para que la persona usuaria radique el documento.",
    },
    "follow_up": {
        "code": "addon_follow_up",
        "name": "Seguimiento del caso",
        "description": "Seguimiento posterior de novedades y trazabilidad del expediente.",
    },
}


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.app_env.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    return response


def _enforce_production_security() -> None:
    if settings.app_env.lower() != "production":
        return
    weak_secrets = {"change-me", "change-me-session", "", None}
    if settings.jwt_secret in weak_secrets or len(settings.jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET inseguro para produccion. Usa un secreto largo y aleatorio.")
    if settings.session_secret in weak_secrets or len(settings.session_secret) < 32:
        raise RuntimeError("SESSION_SECRET inseguro para produccion. Usa un secreto largo y aleatorio.")
    if settings.wompi_environment != "production":
        raise RuntimeError("En produccion WOMPI_ENVIRONMENT debe ser 'production'.")
    if not settings.wompi_event_secret:
        raise RuntimeError("Falta WOMPI_EVENT_SECRET en produccion.")


_enforce_production_security()


def _normalize_user(user: dict[str, Any]) -> UserResponse:
    safe_user = {key: value for key, value in user.items() if key != "password_hash"}
    if safe_user.get("id") is not None:
        safe_user["id"] = str(safe_user["id"])
    safe_user["two_factor_enabled"] = bool(safe_user.get("totp_enabled"))
    return UserResponse(**safe_user)


def _normalize_file(item: dict[str, Any]) -> UploadedFileResponse:
    return UploadedFileResponse(
        id=str(item["id"]),
        case_id=str(item["case_id"]) if item.get("case_id") else None,
        file_kind=item["file_kind"],
        status=item["status"],
        original_name=item["original_name"],
        mime_type=item["mime_type"],
        file_size=item["file_size"],
        created_at=item["created_at"],
        metadata=item.get("metadata") or {},
    )


def _normalize_case(case: dict[str, Any]) -> CaseResponse:
    facts = case.get("facts") or {}
    submission_summary = case.get("submission_summary") or {}
    return CaseResponse(
        id=str(case["id"]),
        user_id=str(case["user_id"]) if case.get("user_id") else None,
        user_name=case["usuario_nombre"],
        user_email=case["usuario_email"],
        user_document=case.get("usuario_documento"),
        user_phone=case.get("usuario_telefono"),
        user_city=case.get("usuario_ciudad"),
        user_department=case.get("usuario_departamento"),
        user_address=case.get("usuario_direccion"),
        category=case["categoria"],
        workflow_type=case.get("workflow_type") or "reclamacion",
        description=case["descripcion"],
        recommended_action=case.get("recommended_action"),
        strategy_text=case.get("strategy_text"),
        facts=facts,
        legal_analysis=case.get("legal_analysis") or {},
        routing=case.get("routing") or {},
        dx_result=facts.get("dx_result") or {},
        pending_questions=facts.get("pending_questions") or [],
        case_route=((case.get("routing") or {}).get("case_route") or facts.get("dx_result", {}).get("route")),
        tutela_procedencia=facts.get("tutela_procedencia") or {},
        source_validation_policy=facts.get("source_validation_policy") or {},
        layer_outputs=facts.get("layer_outputs") or {},
        final_validation=submission_summary.get("final_validation") or {},
        prerequisites=case.get("prerequisites") or [],
        warnings=case.get("warnings") or [],
        status=case.get("estado") or "borrador",
        payment_status=case.get("payment_status") or "pendiente",
        payment_reference=case.get("payment_reference"),
        generated_document=case.get("generated_document"),
        submission_summary=submission_summary,
        attachments=[str(item) for item in (case.get("attachments") or [])],
        created_at=case["created_at"],
        updated_at=case["updated_at"],
    )


def _apply_post_radicado_email_result(
    *,
    case_id: str,
    base_case: dict[str, Any],
    current_status: str,
    manual_contact: dict[str, Any] | None = None,
    guidance: dict[str, Any],
    email_result: dict[str, Any],
    whatsapp_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    updater = repository.update_case_submission if manual_contact is not None else repository.update_case_status
    merged_summary = {
        **(base_case.get("submission_summary") or {}),
        "guidance": guidance,
        "post_radicado_email": email_result,
    }
    if whatsapp_result is not None:
        merged_summary["post_radicado_whatsapp"] = whatsapp_result
    update_kwargs: dict[str, Any] = {
        "status": current_status,
        "submission_summary": merged_summary,
    }
    if manual_contact is not None:
        update_kwargs["manual_contact"] = manual_contact
    updated = updater(case_id, **update_kwargs) or base_case
    repository.create_event(
        case_id=case_id,
        event_type=f"post_radicado_email_{email_result.get('status') or 'processed'}",
        actor_type="system",
        actor_id=None,
        payload=email_result,
    )
    if whatsapp_result is not None:
        repository.create_event(
            case_id=case_id,
            event_type=f"post_radicado_whatsapp_{whatsapp_result.get('status') or 'processed'}",
            actor_type="system",
            actor_id=None,
            payload=whatsapp_result,
        )
    return updated


def _normalize_timeline(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(item["id"]),
            "event_type": item["event_type"],
            "actor_type": item["actor_type"],
            "actor_id": str(item["actor_id"]) if item.get("actor_id") else None,
            "payload": item.get("payload") or {},
            "created_at": item["created_at"],
        }
        for item in items
    ]


def _normalize_attempts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(item["id"]),
            "channel": item["channel"],
            "destination_name": item.get("destination_name"),
            "destination_contact": item.get("destination_contact"),
            "subject": item.get("subject"),
            "cc": item.get("cc") or [],
            "status": item["status"],
            "radicado": item.get("radicado"),
            "response_payload": item.get("response_payload") or {},
            "error_text": item.get("error_text"),
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }
        for item in items
    ]


def _normalize_payment_order(order: dict[str, Any]) -> PaymentOrderResponse:
    return PaymentOrderResponse(
        id=str(order["id"]),
        case_id=str(order["case_id"]),
        user_id=str(order["user_id"]) if order.get("user_id") else None,
        provider=order["provider"],
        environment=order["environment"],
        product_code=order["product_code"],
        product_name=order["product_name"],
        include_filing=order["include_filing"],
        amount_cop=order["amount_cop"],
        amount_in_cents=order["amount_in_cents"],
        currency=order["currency"],
        reference=order["reference"],
        status=order["status"],
        provider_transaction_id=order.get("provider_transaction_id"),
        provider_status=order.get("provider_status"),
        checkout_payload=order.get("checkout_payload") or {},
        approved_at=order.get("approved_at"),
        created_at=order["created_at"],
        updated_at=order["updated_at"],
    )


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_submission_signature(
    signature: dict[str, Any] | None,
    *,
    reviewed_document: bool,
    request: Request | None = None,
) -> dict[str, Any]:
    data = dict(signature or {})
    accepted_at = str(data.get("accepted_at") or "").strip() or datetime.now(timezone.utc).isoformat()
    consent_version = str(data.get("consent_version") or SIMPLE_SIGNATURE_CONSENT_VERSION).strip()
    consent_text = str(
        data.get("consent_text")
        or SIMPLE_SIGNATURE_CONSENT_TEXT
    ).strip()
    ip_address = ""
    user_agent = ""
    if request is not None:
        try:
            ip_address = str((request.client.host if request.client else "") or "").strip()
        except Exception:
            ip_address = ""
        try:
            user_agent = str(request.headers.get("user-agent") or "").strip()
        except Exception:
            user_agent = ""
    normalized = {
        "full_name": str(data.get("full_name") or "").strip(),
        "document_number": str(data.get("document_number") or "").strip(),
        "city": str(data.get("city") or "").strip(),
        "date": str(data.get("date") or "").strip(),
        "accepted": bool(data.get("accepted") or data.get("accept") or data.get("acepta_terminos") or data.get("accepted_terms")),
        "reviewed_document": bool(reviewed_document),
        "accepted_at": accepted_at,
        "consent_version": consent_version,
        "consent_text": consent_text,
        "signature_method": "firma_electronica_simple",
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    if len(normalized["full_name"]) < 4 or len(normalized["document_number"]) < 6 or len(normalized["city"]) < 2 or len(normalized["date"]) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La firma simple esta incompleta.")
    if not normalized["accepted"] or not normalized["reviewed_document"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes revisar el documento y confirmar la firma antes del envio.")
    return normalized


def _merge_intake_into_facts(
    *,
    existing_facts: dict[str, Any],
    form_data: dict[str, Any],
    description: str,
    category: str | None,
) -> dict[str, Any]:
    facts = dict(existing_facts or {})
    facts.pop("quality_follow_up_questions", None)
    entities = list(facts.get("entidades_involucradas") or [])
    target_entity = str(form_data.get("target_entity") or "").strip()
    if target_entity and target_entity not in entities:
        entities.append(target_entity)
    if entities:
        facts["entidades_involucradas"] = entities

    key_dates = str(form_data.get("key_dates") or "").strip()
    if key_dates:
        facts["fechas_mencionadas"] = key_dates

    case_story = str(form_data.get("case_story") or "").strip()
    if case_story:
        facts["hechos_principales"] = case_story
    elif description.strip():
        facts["hechos_principales"] = description.strip()

    concrete_request = str(form_data.get("concrete_request") or "").strip()
    if concrete_request:
        facts["pretension_concreta"] = concrete_request

    if category and not facts.get("problema_central"):
        facts["problema_central"] = category

    facts["intake_form"] = form_data or {}
    return facts


def _pick_preferred_routing_channel(entity: dict[str, Any] | None) -> dict[str, Any] | None:
    channels = list((entity or {}).get("routing_channels") or [])
    if not channels:
        return None
    priority = {"email": 0, "portal_pqrs": 1, "portal": 2, "email_alterno": 3, "telefono": 4}
    channels.sort(key=lambda item: (priority.get(str(item.get("channel") or "").lower(), 9), 0 if item.get("automatable") else 1))
    return channels[0]


def _resolve_entity_directory_prefill(form_data: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(form_data or {})
    target_entity = str(merged.get("target_entity") or "").strip()
    if not target_entity:
        return merged

    try:
        results = search_entity_directory(target_entity, limit=3)
    except Exception:
        return merged
    if not results:
        return merged

    normalized_target = re.sub(r"\s+", " ", target_entity).strip().lower()
    entity = next((item for item in results if str(item.get("name") or "").strip().lower() == normalized_target), results[0])
    preferred_channel = _pick_preferred_routing_channel(entity)

    field_map = {
        "target_entity": entity.get("name"),
        "target_identifier": entity.get("nit"),
        "target_address": entity.get("address"),
        "legal_representative": entity.get("legal_representative"),
        "target_superintendence": entity.get("superintendence"),
        "target_website": entity.get("website"),
    }
    for key, value in field_map.items():
        if value and not str(merged.get(key) or "").strip():
            merged[key] = value

    pqrs_email = next(iter(entity.get("pqrs_emails") or []), "")
    notification_email = next(iter(entity.get("notification_emails") or []), "")
    phone = next(iter(entity.get("phones") or []), "")
    if pqrs_email and not str(merged.get("target_pqrs_email") or "").strip():
        merged["target_pqrs_email"] = pqrs_email
    if notification_email and not str(merged.get("target_notification_email") or "").strip():
        merged["target_notification_email"] = notification_email
    if phone and not str(merged.get("target_phone") or "").strip():
        merged["target_phone"] = phone

    if preferred_channel:
        merged["_entity_channel"] = {
            "channel": preferred_channel.get("channel"),
            "contact": preferred_channel.get("contact"),
            "automatable": preferred_channel.get("automatable"),
            "genera_radicado": preferred_channel.get("genera_radicado"),
            "notes": preferred_channel.get("notes"),
        }
        preferred_contact = str(preferred_channel.get("contact") or "").strip()
        preferred_kind = str(preferred_channel.get("channel") or "").strip().lower()
        if preferred_contact:
            if "@" in preferred_contact and not str(merged.get("target_pqrs_email") or "").strip():
                merged["target_pqrs_email"] = preferred_contact
            elif preferred_contact.startswith("http") and not str(merged.get("target_website") or "").strip():
                merged["target_website"] = preferred_contact
            elif preferred_kind == "telefono" and not str(merged.get("target_phone") or "").strip():
                merged["target_phone"] = preferred_contact

    merged["_resolved_entity_directory"] = {
        "name": entity.get("name"),
        "source": entity.get("source"),
        "routing_channels": entity.get("routing_channels") or [],
    }
    return merged


def _extract_relevant_sentence(text: str, keywords: tuple[str, ...]) -> str:
    for chunk in re.split(r"(?<=[\.\!\?])\s+|\n+", text):
        compact = re.sub(r"\s+", " ", chunk).strip(" .,:;")
        if compact and any(keyword in compact.lower() for keyword in keywords):
            return compact[:240]
    return ""


def _parse_represented_person_identity(value: str) -> dict[str, str]:
    text = str(value or "").strip()
    if not text:
        return {}
    derived: dict[str, str] = {}
    birth_date_match = re.search(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b", text)
    if birth_date_match:
        derived["represented_person_birth_date"] = birth_date_match.group(1)
    age_match = re.search(r"\b(\d{1,2}\s*(?:anos|años))\b", text, flags=re.IGNORECASE)
    if age_match:
        derived["represented_person_age"] = age_match.group(1)
    document_match = re.search(r"\b(?:ti|nuip|rc|registro civil|documento)?\s*#?\s*([0-9.\-]{6,20})\b", text, flags=re.IGNORECASE)
    if document_match:
        derived["represented_person_document"] = document_match.group(1)
    name_candidate = re.sub(r"\b(?:ti|nuip|rc|registro civil|documento)\b", " ", text, flags=re.IGNORECASE)
    name_candidate = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", " ", name_candidate)
    name_candidate = re.sub(r"\b\d{1,2}\s*(?:anos|años)\b", " ", name_candidate, flags=re.IGNORECASE)
    name_candidate = re.sub(r"[0-9.\-#]", " ", name_candidate)
    name_candidate = re.sub(r"\s+", " ", name_candidate).strip(" ,.;:")
    if len(name_candidate.split()) >= 2:
        derived["represented_person_name"] = name_candidate
    return derived


def _infer_acting_capacity_from_text(value: str) -> str:
    normalized = (
        str(value or "")
        .strip()
        .lower()
    )
    if not normalized:
        return ""
    normalized = normalized.translate(str.maketrans({"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n"}))
    if "nombre propio" in normalized:
        return "nombre_propio"
    if any(term in normalized for term in ("representante legal", "tutor", "curador")):
        return "representante_legal"
    if "acudiente" in normalized:
        return "acudiente"
    if re.search(r"(madre|mama|padre|papa)", normalized) and re.search(
        r"(mi hijo|mi hija|del menor|de mi hijo|de mi hija|mi nino|mi nina)",
        normalized,
    ):
        return "madre_padre_menor"
    if any(
        term in normalized
        for term in (
            "agente oficioso",
            "a favor de",
            "en representacion de",
            "por mi mama",
            "por mi madre",
            "por mi papa",
            "por mi padre",
            "por mi esposa",
            "por mi esposo",
            "por mi hermana",
            "por mi hermano",
            "por otra persona",
            "por mi familiar",
        )
    ):
        return "agente_oficioso"
    return ""


def _derive_extra_autofill_fields(
    *,
    form_data: dict[str, Any],
    description: str,
    category: str | None,
    attachment_context: dict[str, Any] | None,
) -> dict[str, Any]:
    combined_text = ". ".join(
        [item for item in [str(description or "").strip(), str((attachment_context or {}).get("combined_text") or "").strip()] if item]
    )
    lowered = combined_text.lower()
    category_key = str(category or "").strip().lower()
    derived: dict[str, Any] = {}

    if not str(form_data.get("prior_claim") or "").strip():
        if any(term in lowered for term in ("radicado", "pqrs", "reclamo", "derecho de peticion", "derecho de petición", "solicitud previa")):
            derived["prior_claim"] = "si"

    if not str(form_data.get("prior_claim_result") or "").strip():
        prior_claim_result = _extract_relevant_sentence(
            combined_text,
            ("neg", "demor", "no respond", "no contest", "no entreg", "sin agenda", "bloque", "rechaz"),
        )
        if prior_claim_result:
            derived["prior_claim_result"] = prior_claim_result

    if not str(form_data.get("urgency_detail") or "").strip():
        urgency_detail = _extract_relevant_sentence(
            combined_text,
            ("urgenc", "riesgo", "dolor", "empeor", "vital", "grave", "suspend", "sin medicamento"),
        )
        if urgency_detail:
            derived["urgency_detail"] = urgency_detail

    if not str(form_data.get("tutela_other_means_detail") or "").strip():
        tutela_other_means_detail = _extract_relevant_sentence(
            combined_text,
            ("reclamo", "peticion", "petición", "radicado", "pqrs", "respond", "contest", "neg", "demor"),
        )
        if tutela_other_means_detail:
            derived["tutela_other_means_detail"] = tutela_other_means_detail

    if not str(form_data.get("special_protection") or "").strip() or str(form_data.get("special_protection")) == "No aplica":
        if any(term in lowered for term in ("menor de edad", "niño", "niña", "adolescente")):
            derived["special_protection"] = "Menor de edad"
        elif any(term in lowered for term in ("adulto mayor", "tercera edad")):
            derived["special_protection"] = "Adulto mayor"
        elif "embaraz" in lowered or "gestante" in lowered:
            derived["special_protection"] = "Embarazada"
        elif any(term in lowered for term in ("discapacidad", "silla de ruedas", "movilidad reducida")):
            derived["special_protection"] = "Discapacidad"

    if not str(form_data.get("tutela_special_protection_detail") or "").strip():
        tutela_special_protection_detail = _extract_relevant_sentence(
            combined_text,
            ("menor de edad", "adulto mayor", "embaraz", "gestante", "discapacidad", "enfermedad grave"),
        )
        if tutela_special_protection_detail:
            derived["tutela_special_protection_detail"] = tutela_special_protection_detail

    if not str(form_data.get("prior_tutela") or "").strip():
        if "tutela anterior" in lowered or "ya presente tutela" in lowered or "ya presenté tutela" in lowered:
            derived["prior_tutela"] = "si"

    if category_key == "salud" and not str(form_data.get("prior_claim") or "").strip():
        if any(term in lowered for term in ("eps", "ips", "autorizacion", "autorización", "farmacia", "agenda")):
            derived["prior_claim"] = "si"

    return derived


def _merge_form_with_attachment_suggestions(
    *,
    form_data: dict[str, Any] | None,
    description: str,
    category: str | None,
    attachment_context: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = _resolve_entity_directory_prefill(form_data or {})
    raw_capacity = str(merged.get("acting_capacity") or "").strip()
    normalized_capacity = raw_capacity.lower()
    allowed_capacities = {"", "nombre_propio", "agente_oficioso", "representante_legal", "acudiente", "madre_padre_menor"}
    if raw_capacity and normalized_capacity not in allowed_capacities:
        inferred_from_field = _infer_acting_capacity_from_text(raw_capacity)
        if inferred_from_field:
            merged["acting_capacity"] = inferred_from_field
        for key, value in _parse_represented_person_identity(raw_capacity).items():
            if value and not str(merged.get(key) or "").strip():
                merged[key] = value
    identity_blob = str(merged.get("represented_person_identity") or "").strip()
    if identity_blob:
        for key, value in _parse_represented_person_identity(identity_blob).items():
            if value and not str(merged.get(key) or "").strip():
                merged[key] = value
    category_key = str(category or "").strip().lower()
    combined_text = ". ".join(
        [
            item
            for item in [
                str(description or "").strip(),
                str(merged.get("case_story") or "").strip(),
                str((attachment_context or {}).get("combined_text") or "").strip(),
            ]
            if item
        ]
    )
    if str(merged.get("acting_capacity") or "").strip().lower() in {"", "nombre_propio"}:
        inferred_from_text = _infer_acting_capacity_from_text(combined_text)
        if inferred_from_text and inferred_from_text != "nombre_propio":
            merged["acting_capacity"] = inferred_from_text
    suggestions = suggest_fields_from_context(
        category=category,
        description=description,
        form_data=merged,
        attachment_context=attachment_context,
    )
    for key, value in (attachment_context or {}).get("typed_suggestions", {}).items():
        if value and not str(merged.get(key) or "").strip() and not suggestions.get(key):
            suggestions[key] = value
    suggestions.update(
        {
            key: value
            for key, value in _derive_extra_autofill_fields(
                form_data=merged,
                description=description,
                category=category,
                attachment_context=attachment_context,
            ).items()
            if not str(merged.get(key) or "").strip()
        }
    )
    for key, value in list(suggestions.items()):
        cleaned = str(value or "").strip()
        if key == "disputed_charge":
            cleaned = re.split(r"\s+(?:el|por|desde|segun)\s+(?=\d|\$)", cleaned, maxsplit=1)[0].strip(" .,:;")
            cleaned = re.sub(r"\s+el$", "", cleaned, flags=re.IGNORECASE).strip(" .,:;")
        elif key == "treatment_needed":
            cleaned = re.split(r"\s+(?:el|para|desde)\s+(?=\d|[A-Z])", cleaned, maxsplit=1)[0].strip(" .,:;")
            if category_key == "salud" and re.search(r"\b(banco|davivienda|bancolombia|seguro|cobro|cargo)\b", cleaned, flags=re.IGNORECASE):
                cleaned = ""
        elif key == "target_entity":
            cleaned = re.split(r"\s+(?:cobro|nego|niega|reporto|bloqueo|debito|cargo)\b", cleaned, maxsplit=1)[0].strip(" .,:;")
        if cleaned:
            suggestions[key] = cleaned
        else:
            suggestions.pop(key, None)
    for key, value in suggestions.items():
        if not str(merged.get(key) or "").strip() and str(value or "").strip():
            merged[key] = value
    if suggestions:
        merged["_autofill"] = suggestions
    return merged


def _refresh_verified_case_context(case: dict[str, Any]) -> dict[str, Any]:
    facts = dict(case.get("facts") or {})
    legal_analysis = dict(case.get("legal_analysis") or {})
    source_validation_policy = facts.get("source_validation_policy") or build_source_validation_policy()
    resolved_support = resolve_verified_legal_support(
        recommended_action=case.get("recommended_action"),
        workflow_type=case.get("workflow_type"),
        category=case.get("categoria") or case.get("category"),
        legal_analysis=legal_analysis,
    )
    source_validation_policy = {
        **source_validation_policy,
        **resolved_support,
    }
    source_validation_policy["legal_basis_verified_summary"] = build_verified_legal_basis_text(source_validation_policy)
    facts["source_validation_policy"] = source_validation_policy
    legal_analysis = sanitize_legal_analysis(
        legal_analysis=legal_analysis,
        source_validation_policy=source_validation_policy,
    )
    legal_analysis["legal_basis_verified_summary"] = source_validation_policy["legal_basis_verified_summary"]
    agent_state = build_health_agent_state(
        category=case.get("categoria") or case.get("category") or "",
        workflow_type=case.get("workflow_type") or "",
        recommended_action=case.get("recommended_action") or "",
        description=case.get("descripcion") or "",
        facts=facts,
    )
    if agent_state:
        facts["agent_state"] = agent_state
    case["facts"] = facts
    case["legal_analysis"] = legal_analysis
    return case


def _payment_entitlements_from_orders(orders: list[dict[str, Any]]) -> dict[str, Any]:
    approved = [item for item in orders if _lower(item.get("status")) == "approved"]
    approved_codes = {_lower(item.get("product_code")) for item in approved}
    document_paid = bool(approved)
    filing_bundle_paid = "addon_filing_bundle" in approved_codes
    filing_paid = any(
        bool(item.get("include_filing"))
        or _lower(item.get("product_code")) == "addon_filing_auto"
        or filing_bundle_paid
        for item in approved
    )
    guide_paid = filing_paid or "addon_filing_guide" in approved_codes
    follow_up_paid = filing_bundle_paid or "addon_follow_up" in approved_codes
    return {
        "document_paid": document_paid,
        "filing_bundle_paid": filing_bundle_paid,
        "filing_auto_paid": filing_paid,
        "filing_guide_paid": guide_paid,
        "follow_up_paid": follow_up_paid,
    }


def _payment_summary_from_orders(orders: list[dict[str, Any]]) -> dict[str, Any]:
    if not orders:
        return {}

    latest = orders[0]
    approved = [item for item in orders if _lower(item.get("status")) == "approved"]
    latest_approved = approved[0] if approved else None
    source = latest_approved or latest
    return {
        "latest_reference": source.get("reference"),
        "latest_status": _lower(source.get("status") or "pending"),
        "latest_provider_status": source.get("provider_status"),
        "latest_product_name": source.get("product_name"),
        "latest_amount_cop": source.get("amount_cop"),
        "latest_include_filing": bool(source.get("include_filing")),
        "latest_provider_transaction_id": source.get("provider_transaction_id"),
        "latest_approved_at": source.get("approved_at"),
        "latest_created_at": source.get("created_at"),
        "orders_count": len(orders),
        "approved_orders_count": len(approved),
        "has_webhook_payload": bool(source.get("webhook_payload")),
    }


def _is_ai_owned_quality_issue(issue: object) -> bool:
    lowered = str(issue or "").lower()
    ai_owned_patterns = (
        "jurisprudencia",
        "soporte oficial verificado",
        "referencias juridicas no verificadas automaticamente",
        "citas no verificadas",
        "fuentes verificadas",
        "sustento juridico",
        "sustento jurídico",
        "la ia debe reforzar",
        "la ia debe depurar",
        "calidad juridica automatica",
        "calidad jurídica automatica",
    )
    return any(pattern in lowered for pattern in ai_owned_patterns)


def _blocking_issue_fix_location(issue: object, recommended_action: str = "") -> str:
    lowered = str(issue or "").lower()
    action = str(recommended_action or "").lower()
    if "pretension concreta" in lowered:
        return "Solucion concreta que necesitas"
    if any(token in lowered for token in ["eps", "ips", "entidad accionada", "entidad destinataria"]):
        return "Entidad y canal de radicacion"
    if any(token in lowered for token in ["diagnostico", "condicion medica", "condición médica"]):
        return "Detalle del caso de salud"
    if any(token in lowered for token in ["medicamento", "servicio concreto", "procedimiento requerido", "tratamiento"]):
        return "Detalle del caso de salud"
    if any(token in lowered for token in ["riesgo", "urgencia", "dano", "daño", "afectacion actual", "afectación actual"]):
        return "Paso de tutela y urgencia actual" if "tutela" in action else "Detalle del caso"
    if any(token in lowered for token in ["gestion previa", "subsidiariedad", "reclamo previo", "peticion o medida previa", "petición o medida previa"]):
        return "Paso de tutela y urgencia actual" if "tutela" in action else "Completa datos del caso"
    if any(token in lowered for token in ["no temeridad", "juramento", "tutela previa"]):
        return "Preguntas finas para tutela"
    if any(token in lowered for token in ["menor", "representada", "representado", "fecha de nacimiento", "documento de la persona"]):
        return "Preguntas finas para tutela"
    if any(token in lowered for token in ["soporte medico", "historia clinica", "historia clínica", "orden medica", "orden médica", "pruebas medicas", "pruebas médicas"]):
        return "Pruebas y anexos"
    if "peticion" in action:
        return "Paso de derecho de peticion"
    return "Completa datos del caso"


def _format_blocking_detail_with_actions(
    *,
    prefix: str,
    blocking_issues: list[str],
    recommended_action: str = "",
) -> str:
    detail_parts = list(blocking_issues or [])
    actionable_text = [
        f"{issue} (completalo en: {_blocking_issue_fix_location(issue, recommended_action)})"
        for issue in detail_parts[:4]
    ]
    if actionable_text:
        detail_parts = detail_parts + ["Corrige ahora: " + " | ".join(actionable_text)]
    return prefix + " | ".join(detail_parts)


def _build_quality_follow_up_questions(blocking_issues: list[str]) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    def add(question_id: str, question: str, reason: str, *, field: str | None = None) -> None:
        if question_id in seen_ids:
            return
        seen_ids.add(question_id)
        questions.append(
            {
                "id": question_id,
                "question": question,
                "reason": reason,
                "priority": "alta",
                "field": field,
                "route": "B",
                "responded": False,
            }
        )

    for issue in blocking_issues or []:
        issue_text = str(issue or "").strip().lower()
        if "mezcla una persona accionante con una paciente distinta" in issue_text:
            add(
                "quality_representation",
                "Confirma si presentas la tutela en nombre propio o por otra persona. Si es por otra persona, indica nombre completo del paciente, documento, edad y en que calidad actuas.",
                "Hay una inconsistencia entre la persona accionante y la paciente protegida.",
                field="acting_capacity",
            )
        if "cronologia de la tutela contiene lineas vacias" in issue_text or "hechos demasiado genericos" in issue_text:
            add(
                "quality_chronology",
                "Escribe 3 a 6 hitos cronologicos con fecha, especialidad o medico y que paso en cada consulta o gestion ante la EPS.",
                "La cronologia actual sigue demasiado generica para sostener la tutela.",
                field="key_dates",
            )
        if "frases plantilla o texto crudo del intake" in issue_text:
            add(
                "quality_closed_facts",
                "Dime con precision cual es el servicio, medicamento o decision medica que necesitas y cual fue la barrera concreta que puso la EPS o la IPS.",
                "Todavia faltan hechos clinicos y juridicos cerrados.",
                field="treatment_needed",
            )
        if "formulaciones crudas o errores de redaccion del usuario" in issue_text:
            add(
                "quality_clean_request",
                "Confirma cual orden concreta quieres pedir al juez: autorizacion de medicamento, junta medica, valoracion prioritaria, cirugia o tratamiento integral.",
                "La pretension todavia esta ambigua o demasiado cruda.",
                field="concrete_request",
            )
    return questions


def _enrich_architecture_outputs(
    *,
    category: str,
    description: str,
    workflow: dict[str, Any],
    facts: dict[str, Any],
    legal_analysis: dict[str, Any],
    routing: dict[str, Any],
    intake_review: dict[str, Any],
    preview_gate: dict[str, Any],
    document_rule_review: dict[str, Any],
    prior_actions: list[str],
    final_validation: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source_validation_policy = facts.get("source_validation_policy") or build_source_validation_policy()
    resolved_support = resolve_verified_legal_support(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        category=category,
        legal_analysis=legal_analysis,
    )
    source_validation_policy = {
        **source_validation_policy,
        **resolved_support,
    }
    source_validation_policy["legal_basis_verified_summary"] = build_verified_legal_basis_text(source_validation_policy)
    tutela_procedencia = (
        evaluate_tutela_procedencia(description=description, facts=facts, prior_actions=prior_actions)
        if workflow["workflow_type"] == "tutela"
        else {}
    )
    pending_questions = collect_pending_questions(
        category=category,
        workflow_type=workflow["workflow_type"],
        description=description,
        facts=facts,
        prior_actions=prior_actions,
    )
    dx_result = build_dx_result(
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        facts=facts,
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        tutela_procedencia=tutela_procedencia or None,
        pending_questions=pending_questions,
    )
    layer_outputs = build_layer_outputs(
        dx_result=dx_result,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        pending_questions=pending_questions,
        tutela_procedencia=tutela_procedencia or None,
        final_validation=final_validation,
    )
    enriched_facts = dict(facts)
    enriched_facts["source_validation_policy"] = source_validation_policy
    enriched_facts["tutela_procedencia"] = tutela_procedencia
    enriched_facts["pending_questions"] = pending_questions
    enriched_facts["dx_result"] = dx_result
    enriched_facts["layer_outputs"] = layer_outputs
    agent_state = build_health_agent_state(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=description,
        facts=enriched_facts,
    )
    if agent_state:
        enriched_facts["agent_state"] = agent_state

    enriched_legal_analysis = dict(legal_analysis or {})
    enriched_legal_analysis = sanitize_legal_analysis(
        legal_analysis=enriched_legal_analysis,
        source_validation_policy=source_validation_policy,
    )
    if tutela_procedencia:
        enriched_legal_analysis["tutela_procedencia_preliminar"] = tutela_procedencia
    enriched_legal_analysis["legal_basis_verified_summary"] = source_validation_policy["legal_basis_verified_summary"]

    enriched_routing = dict(routing or {})
    enriched_routing["case_route"] = dx_result.get("route")
    enriched_routing["requires_human_review"] = dx_result.get("requires_human_review", False)
    enriched_routing["urgency_level"] = dx_result.get("urgency_level")
    return enriched_facts, enriched_legal_analysis, enriched_routing


def _rehydrate_case_intelligence(case: dict[str, Any]) -> dict[str, Any]:
    category = case.get("categoria") or case.get("category") or ""
    case_id = str(case["id"])
    prior_actions = [item["id"] for item in (case.get("prerequisites") or []) if item.get("completed")]
    attachment_records = repository.list_files_for_case(case_id)
    attachment_context = build_attachment_context(attachment_records)
    description = case.get("descripcion") or ""
    enriched_description = enrich_description_with_attachment_context(description, attachment_context)
    existing_facts = case.get("facts") or {}
    enriched_form_data = _merge_form_with_attachment_suggestions(
        form_data=(existing_facts.get("intake_form") or {}),
        description=enriched_description,
        category=category,
        attachment_context=attachment_context,
    )
    facts = _merge_intake_into_facts(
        existing_facts=existing_facts,
        form_data=enriched_form_data,
        description=enriched_description,
        category=category,
    )
    legal_analysis = case.get("legal_analysis") or {}
    workflow = infer_workflow(
        category=category,
        description=enriched_description,
        facts=facts,
        legal_analysis=legal_analysis,
        prior_actions=prior_actions,
    )
    routing = build_routing(
        category=category,
        city=case.get("usuario_ciudad") or "",
        department=case.get("usuario_departamento") or "",
        facts=facts,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
    )
    strategy = build_strategy_text(
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        legal_analysis=legal_analysis,
        warnings=workflow["warnings"],
    )
    intake_review = validate_intake(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=facts,
        prior_actions=prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=facts,
        prior_actions=prior_actions,
        stage="save",
    )
    document_rule_review = evaluate_document_rule(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=facts,
    )
    facts["intake_review"] = intake_review
    facts["preview_gate"] = preview_gate
    facts["document_rule_review"] = document_rule_review
    facts["attachment_intelligence"] = attachment_context
    facts["uploaded_evidence_files"] = [
        {
            "id": str(item.get("id")),
            "original_name": str(item.get("original_name") or ""),
            "file_kind": str(item.get("file_kind") or ""),
            "relative_path": str(item.get("relative_path") or ""),
            "mime_type": str(item.get("mime_type") or ""),
            "file_size": int(item.get("file_size") or 0),
        }
        for item in attachment_records
        if item.get("original_name")
    ]
    facts["autofill_suggestions"] = enriched_form_data.get("_autofill") or {}
    facts, legal_analysis, routing = _enrich_architecture_outputs(
        category=category,
        description=enriched_description,
        workflow=workflow,
        facts=facts,
        legal_analysis=legal_analysis,
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        prior_actions=prior_actions,
    )
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
        + facts.get("dx_result", {}).get("blocking_reasons", [])
        + facts.get("dx_result", {}).get("warnings", [])
    )
    updated = repository.update_case_intake(
        case_id,
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=facts,
        legal_analysis=legal_analysis,
        routing=routing,
        prerequisites=workflow["prerequisites"],
        warnings=list(dict.fromkeys(combined_warnings)),
        recommended_action=workflow["recommended_action"],
        strategy_text=strategy,
    )
    return updated or {
        **case,
        "workflow_type": workflow["workflow_type"],
        "descripcion": enriched_description,
        "facts": facts,
        "legal_analysis": legal_analysis,
        "routing": routing,
        "prerequisites": workflow["prerequisites"],
        "warnings": list(dict.fromkeys(combined_warnings)),
        "recommended_action": workflow["recommended_action"],
        "strategy_text": strategy,
    }


def _reconcile_case_payment(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case["id"])
    orders = repository.list_payment_orders_for_case(case_id)
    if not orders:
        return case

    latest = orders[0]
    order_status = str(latest.get("status") or "pending").lower()
    desired_case_status = {
        "approved": "pagado",
        "declined": "rechazado",
        "error": "error",
        "voided": "anulado",
        "pending": "pendiente",
    }.get(order_status)
    if not desired_case_status:
        return case

    current_status = case.get("payment_status") or "pendiente"
    current_reference = case.get("payment_reference")
    latest_reference = latest.get("reference")

    should_update = (
        desired_case_status == "pagado" and current_status != "pagado"
    ) or (
        current_status == "pendiente" and desired_case_status != current_status
    ) or (
        latest_reference and current_reference != latest_reference and desired_case_status == current_status
    )

    if not should_update:
        return case

    updated = repository.update_case_payment(
        case_id,
        str(latest_reference or current_reference or ""),
        payment_status=desired_case_status,
    )
    return updated or case


def _snapshot_case_detail(case: dict[str, Any]) -> CaseDetailResponse:
    case = _reconcile_case_payment(case)
    files = repository.list_files_for_case(str(case["id"]))
    orders = repository.list_payment_orders_for_case(str(case["id"]))
    attempts = repository.list_submission_attempts(str(case["id"]))
    events = repository.list_case_events(str(case["id"]))
    case["submission_summary"] = {
        **(case.get("submission_summary") or {}),
        "payment_entitlements": _payment_entitlements_from_orders(orders),
        "payment_summary": _payment_summary_from_orders(orders),
    }
    return CaseDetailResponse(
        case=_normalize_case(case),
        files=[_normalize_file(item) for item in files],
        submission_attempts=_normalize_attempts(attempts),
        timeline=_normalize_timeline(events),
    )


def _is_internal(user: dict[str, Any]) -> bool:
    return user.get("role") == "internal"


def _parse_whatsapp_abandonment_windows() -> list[int]:
    raw = str(settings.whatsapp_abandonment_windows or "").strip()
    values: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            value = int(token)
        except ValueError:
            continue
        if value > 0:
            values.append(value)
    return sorted(set(values)) or [30, 120]


def _is_within_whatsapp_window(now_utc: datetime) -> bool:
    local_now = now_utc.astimezone(settings.app_tz)
    hour = local_now.hour
    start = int(settings.whatsapp_abandonment_start_hour)
    end = int(settings.whatsapp_abandonment_end_hour)
    if start == end:
        return True
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


def _build_guest_resume_url(case: dict[str, Any]) -> str:
    token = str(case.get("public_token") or "").strip()
    case_id = str(case.get("id") or "").strip()
    if token and case_id:
        return f"{settings.frontend_url.rstrip('/')}/dashboard?case_id={case_id}&token={token}"
    return f"{settings.frontend_url.rstrip('/')}/diagnostico"


def _run_whatsapp_abandonment_reminders(*, dry_run: bool = False) -> dict[str, Any]:
    now_utc = datetime.now(timezone.utc)
    windows = _parse_whatsapp_abandonment_windows()
    if not settings.whatsapp_abandonment_enabled:
        return {"ok": True, "status": "disabled", "windows": windows, "processed": 0, "sent": 0}
    if not _is_within_whatsapp_window(now_utc):
        return {"ok": True, "status": "outside_window", "windows": windows, "processed": 0, "sent": 0}

    all_cases = repository.list_internal_cases()
    run_limit = max(1, int(settings.whatsapp_abandonment_run_limit))
    daily_limit = max(1, int(settings.whatsapp_abandonment_daily_limit))
    day_start = now_utc.astimezone(settings.app_tz).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)

    sent_today = 0
    sent_records: list[dict[str, Any]] = []
    skipped_records: list[dict[str, Any]] = []

    candidate_cases = sorted(all_cases, key=lambda item: item.get("created_at") or now_utc)
    for case in candidate_cases:
        if sent_today >= daily_limit or len(sent_records) >= run_limit:
            break
        if str(case.get("payment_status") or "").lower() == "pagado":
            continue
        if str(case.get("estado") or "").lower() not in {"diagnosticado", "borrador", "pendiente", "pagado_pendiente_intake"}:
            continue
        if not str(case.get("usuario_telefono") or "").strip():
            continue

        created_at = case.get("created_at")
        if not isinstance(created_at, datetime):
            continue
        elapsed_minutes = int((now_utc - created_at).total_seconds() // 60)
        if elapsed_minutes <= 0:
            continue

        events = repository.list_case_events(str(case.get("id")))
        reminder_events = [
            event
            for event in events
            if str(event.get("event_type") or "") == "whatsapp_diagnosis_reminder_sent"
            and isinstance(event.get("created_at"), datetime)
            and event["created_at"] >= day_start
        ]
        sent_today += len(reminder_events)
        sent_stages = {
            int((event.get("payload") or {}).get("stage_minutes"))
            for event in reminder_events
            if str((event.get("payload") or {}).get("stage_minutes") or "").isdigit()
        }
        stage_due = next((stage for stage in windows if elapsed_minutes >= stage and stage not in sent_stages), None)
        if stage_due is None:
            skipped_records.append({"case_id": str(case.get("id")), "reason": "no_due_stage", "elapsed_minutes": elapsed_minutes})
            continue
        if sent_today >= daily_limit:
            skipped_records.append({"case_id": str(case.get("id")), "reason": "daily_limit_reached"})
            break

        resume_url = _build_guest_resume_url(case)
        if dry_run:
            sent_records.append(
                {
                    "case_id": str(case.get("id")),
                    "stage_minutes": stage_due,
                    "recipient": str(case.get("usuario_telefono") or ""),
                    "resume_url": resume_url,
                    "status": "dry_run",
                }
            )
            continue

        result = send_diagnosis_abandonment_whatsapp(
            phone=case.get("usuario_telefono"),
            case=case,
            reminder_minutes=stage_due,
            resume_url=resume_url,
        )
        payload = {
            "stage_minutes": stage_due,
            "elapsed_minutes": elapsed_minutes,
            "recipient": result.get("recipient"),
            "status": result.get("status"),
            "reason": result.get("reason"),
        }
        repository.create_event(
            case_id=str(case.get("id")),
            event_type="whatsapp_diagnosis_reminder_sent" if result.get("status") == "sent" else "whatsapp_diagnosis_reminder_error",
            actor_type="system",
            actor_id=None,
            payload=payload,
        )
        sent_records.append(
            {
                "case_id": str(case.get("id")),
                "stage_minutes": stage_due,
                "recipient": result.get("recipient"),
                "status": result.get("status"),
                "reason": result.get("reason"),
            }
        )
        if result.get("status") == "sent":
            sent_today += 1

    return {
        "ok": True,
        "status": "completed",
        "dry_run": dry_run,
        "windows": windows,
        "sent_today": sent_today,
        "run_limit": run_limit,
        "daily_limit": daily_limit,
        "processed": len(sent_records) + len(skipped_records),
        "sent": len([item for item in sent_records if item.get("status") in {"sent", "dry_run"}]),
        "records": sent_records[: run_limit * 2],
        "skipped": skipped_records[:20],
    }


def _is_qa_test_user(user: dict[str, Any]) -> bool:
    return str(user.get("email") or "").strip().lower() in set(settings.qa_test_emails or [])


def _require_profile(user: dict[str, Any]) -> None:
    if not user_profile_complete(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completa tu perfil antes de crear, radicar o generar documentos.",
        )


def get_current_user(
    authorization: str = Header(default=""),
    admin_session: str | None = Cookie(default=None, alias="admin_session"),
) -> dict[str, Any]:
    token = ""
    if authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "", 1).strip()
    elif admin_session:
        token = str(admin_session).strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión requerida.")
    try:
        payload = decode_token(token, settings.jwt_secret)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = repository.get_user_by_id(str(payload["sub"]))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado.")
    return user


def get_internal_user(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if not _is_internal(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso interno requerido.")
    return current_user


def _role_for_email(email: str) -> str:
    normalized_email = str(email or "").strip().lower()
    normalized_email = normalized_email.replace("–", "-").replace("—", "-").replace("−", "-")
    return "internal" if normalized_email in settings.internal_admin_emails else "citizen"


def _normalize_email_input(email: str) -> str:
    return str(email or "").strip().lower().replace("–", "-").replace("—", "-").replace("−", "-")


def _totp_issuer() -> str:
    return str(settings.app_name or "123tutela").strip() or "123tutela"


def _verify_internal_second_factor(user: dict[str, Any], *, otp_code: str | None = None, recovery_code: str | None = None) -> bool:
    if not bool(user.get("totp_enabled")):
        return True

    secret = str(user.get("totp_secret") or "").strip()
    if secret and otp_code and verify_totp_code(secret, otp_code):
        repository.touch_user_totp_used(str(user["id"]))
        return True

    recovery_hashes = [str(item) for item in (user.get("totp_recovery_hashes") or []) if str(item)]
    if recovery_code:
        candidate = hash_recovery_code(recovery_code)
        if candidate in recovery_hashes:
            remaining = [item for item in recovery_hashes if item != candidate]
            repository.update_user_totp_recovery_hashes(str(user["id"]), remaining)
            return True
    return False


def _get_guest_case_or_404(case_id: str, public_token: str) -> dict[str, Any]:
    case = repository.get_case_by_id_and_public_token(case_id, public_token)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso publico no encontrado.")
    return case


def _merge_submission_summary(case: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return {
        **(case.get("submission_summary") or {}),
        **extra,
    }


def _build_marketing_suggestions(
    *,
    funnel: dict[str, int],
    event_counts: dict[str, int],
    drop_alerts: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    visitors = max(int(event_counts.get("page_views") or 0), 1)
    cta_clicks = int(event_counts.get("cta_clicks") or 0)
    diagnosis_starts = int(event_counts.get("diagnosis_starts") or 0)
    checkout_starts = int(event_counts.get("checkout_starts") or 0)
    paid = int(funnel.get("paid_cases") or 0)
    intake_submitted = int(funnel.get("intake_submitted") or 0)

    suggestions: list[dict[str, str]] = []
    cta_rate = cta_clicks / visitors
    checkout_rate = checkout_starts / max(diagnosis_starts, 1)
    pay_rate = paid / max(checkout_starts, 1)
    intake_rate = intake_submitted / max(paid, 1)

    if cta_rate < 0.12:
        suggestions.append({
            "priority": "alta",
            "title": "Mejorar clic al CTA principal",
            "action": "Probar 2 variantes de titular y CTA (A/B) en home durante 7 dias; mantener la que supere 12% de clic.",
        })
    if checkout_rate < 0.55:
        suggestions.append({
            "priority": "alta",
            "title": "Reducir fuga entre diagnóstico y pago",
            "action": "Simplificar pantalla de pago a un solo mensaje de valor, mostrar precio final sin fricción y recordar rifa/codigo unico.",
        })
    if pay_rate < 0.45:
        suggestions.append({
            "priority": "alta",
            "title": "Subir conversión de checkout a pago",
            "action": "Agregar prueba social y garantía operativa junto al botón de pago, más seguimiento por WhatsApp para abandono de pago.",
        })
    if intake_rate < 0.65:
        suggestions.append({
            "priority": "media",
            "title": "Completar más expedientes post-pago",
            "action": "Autocompletar datos básicos, mostrar checklist mínimo por caso y recordatorio automático a los 30 y 120 minutos.",
        })
    for alert in drop_alerts or []:
        label = str(alert.get("label") or "segmento")
        stage = str(alert.get("stage") or "embudo")
        drop_pct = int(alert.get("drop_pct") or 0)
        suggestions.append({
            "priority": "alta",
            "title": f"Caida detectada en {label}",
            "action": f"{stage} cayo {drop_pct}% vs periodo anterior. Activa variante de CTA en admin y valida durante 7 dias.",
        })
    if not suggestions:
        suggestions.append({
            "priority": "media",
            "title": "Sistema estable",
            "action": "Mantener medición semanal y correr experimentos pequeños por canal de adquisición para mejorar CAC y conversión.",
        })
    return suggestions[:5]


def _detect_period_drop(*, current: int, previous: int, threshold_pct: int = 25) -> int:
    if previous <= 0:
        return 0
    delta = current - previous
    pct = int(round((delta / previous) * 100))
    return pct if pct <= -threshold_pct else 0


def _build_drop_alerts(current_rows: list[dict[str, Any]], previous_rows: list[dict[str, Any]], label: str) -> list[dict[str, Any]]:
    prev_map = {str(row.get("key") or ""): row for row in previous_rows}
    alerts: list[dict[str, Any]] = []
    for row in current_rows:
        key = str(row.get("key") or "")
        prev = prev_map.get(key)
        if not prev:
            continue
        current_diag = int(row.get("diagnosis_starts") or 0)
        prev_diag = int(prev.get("diagnosis_starts") or 0)
        drop_diag = _detect_period_drop(current=current_diag, previous=prev_diag)
        if drop_diag:
            alerts.append({
                "type": "drop",
                "dimension": label,
                "key": key,
                "label": f"{label}: {key}",
                "stage": "Diagnostico iniciado",
                "drop_pct": abs(drop_diag),
                "current": current_diag,
                "previous": prev_diag,
            })
        current_checkout = int(row.get("checkout_starts") or 0)
        prev_checkout = int(prev.get("checkout_starts") or 0)
        drop_checkout = _detect_period_drop(current=current_checkout, previous=prev_checkout)
        if drop_checkout:
            alerts.append({
                "type": "drop",
                "dimension": label,
                "key": key,
                "label": f"{label}: {key}",
                "stage": "Checkout iniciado",
                "drop_pct": abs(drop_checkout),
                "current": current_checkout,
                "previous": prev_checkout,
            })
    return alerts[:8]


def _guest_status_response(case: dict[str, Any]) -> GuestCaseStatusResponse:
    files = repository.list_files_for_case(str(case["id"]))
    orders = repository.list_payment_orders_for_case(str(case["id"]))
    summary = case.get("submission_summary") or {}
    latest_order = orders[0] if orders else None
    return GuestCaseStatusResponse(
        case=_normalize_case(_reconcile_case_payment(case)),
        public_token=str(case.get("public_token") or summary.get("public_token") or ""),
        customer_summary={
            **(summary.get("customer_summary") or build_customer_summary(case)),
            "customer_case": summary.get("customer_case") or {},
            "invoice": summary.get("invoice") or {},
            "raffle": summary.get("raffle") or {},
        },
        customer_guide=summary.get("customer_guide") or build_customer_guide(case),
        delivery_package=summary.get("delivery_package") or {},
        latest_payment={
            "reference": latest_order.get("reference") if latest_order else case.get("payment_reference"),
            "status": latest_order.get("status") if latest_order else case.get("payment_status"),
            "approved_at": latest_order.get("approved_at") if latest_order else None,
            "customer_case": summary.get("customer_case") or {},
            "invoice": summary.get("invoice") or {},
            "raffle": summary.get("raffle") or {},
        },
        files=[_normalize_file(item) for item in files],
    )


def _persist_guest_ops(case: dict[str, Any]) -> dict[str, Any]:
    result = sync_case_to_ops(case)
    merged = _merge_submission_summary(case, ops_sync=result)
    updated = repository.update_case_status(str(case["id"]), status=case.get("estado") or "pagado_en_revision", submission_summary=merged)
    return updated or case


def _latest_payment_order(case_id: str) -> dict[str, Any] | None:
    orders = repository.list_payment_orders_for_case(case_id)
    return orders[0] if orders else None


def _build_payment_token(
    case: dict[str, Any],
    approved_at: datetime | None,
    label: str,
    *,
    length: int = 8,
) -> str:
    latest_order = _latest_payment_order(str(case.get("id") or ""))
    raw = "|".join(
        [
            label,
            str(case.get("id") or ""),
            str(case.get("public_token") or ""),
            str(case.get("payment_reference") or ""),
            str((latest_order or {}).get("reference") or ""),
            (approved_at or datetime.now(timezone.utc)).isoformat(),
            settings.jwt_secret,
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()[:length]


def _build_customer_case_code(case: dict[str, Any], approved_at: datetime | None) -> str:
    period = (approved_at or datetime.now(timezone.utc)).strftime("%y%m")
    token = _build_payment_token(case, approved_at, "customer_case", length=8)
    return f"HPM-CAS-{period}-{token}"


def _build_invoice_number(case: dict[str, Any], approved_at: datetime | None) -> str:
    period = (approved_at or datetime.now(timezone.utc)).strftime("%Y%m")
    token = _build_payment_token(case, approved_at, "invoice", length=8)
    return f"HPM-FAC-{period}-{token}"


def _build_raffle_code(case: dict[str, Any], approved_at: datetime | None) -> str:
    period = (approved_at or datetime.now(timezone.utc)).strftime("%y%m")
    token = _build_payment_token(case, approved_at, "raffle", length=8)
    return f"HPM-RIFA-{period}-{token}"


def _ensure_payment_artifacts(case_id: str) -> dict[str, Any] | None:
    case = repository.get_case_by_id(case_id)
    if not case or case.get("payment_status") != "pagado":
        return case
    latest_order = _latest_payment_order(case_id)
    summary = dict(case.get("submission_summary") or {})
    existing_invoice = summary.get("invoice") or {}
    existing_raffle = summary.get("raffle") or {}
    existing_customer_case = summary.get("customer_case") or {}
    if existing_invoice.get("number") and existing_raffle.get("code") and existing_customer_case.get("code"):
        return case

    approved_at = latest_order.get("approved_at") if latest_order else None
    customer_case_code = existing_customer_case.get("code") or _build_customer_case_code(case, approved_at)
    invoice_number = existing_invoice.get("number") or _build_invoice_number(case, approved_at)
    raffle_code = existing_raffle.get("code") or _build_raffle_code(case, approved_at)
    amount_cop = int((latest_order or {}).get("amount_cop") or BASE_SERVICE_PRICE_COP)
    period_label = (approved_at or datetime.now(timezone.utc)).strftime("%Y-%m")

    invoice_title = f"Factura {invoice_number}"
    invoice_text = "\n".join(
        [
            f"Expediente HazloPorMi: {customer_case_code}",
            f"Factura operativa: {invoice_number}",
            f"Fecha de pago: {(approved_at or datetime.now(timezone.utc)).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Cliente: {case.get('usuario_nombre') or ''}",
            f"Email: {case.get('usuario_email') or ''}",
            f"Telefono: {case.get('usuario_telefono') or ''}",
            f"Servicio: {SERVICE_PRODUCT_NAME}",
            f"Categoria: {case.get('categoria') or ''}",
            f"Documento sugerido: {case.get('recommended_action') or ''}",
            f"Referencia de pago: {latest_order.get('reference') if latest_order else case.get('payment_reference') or ''}",
            f"Valor pagado: {amount_cop} COP",
            "",
            f"Codigo unico de participacion promocional: {raffle_code}",
            f"Periodo promocional: {period_label}",
            "Cada pago aprobado genera un codigo unico de referencia promocional.",
        ]
    )
    invoice_filename = f"{invoice_number}.pdf"
    invoice_dir = ensure_upload_root() / "invoices" / case_id
    invoice_dir.mkdir(parents=True, exist_ok=True)
    invoice_path = invoice_dir / invoice_filename
    invoice_path.write_bytes(render_text_pdf(title=invoice_title, text=invoice_text))
    relative_path = invoice_path.relative_to(ensure_upload_root()).as_posix()

    if not existing_invoice.get("relative_path"):
        repository.create_case_file(
            case_id=case_id,
            uploaded_by=None,
            file_kind="invoice_document",
            original_name=invoice_filename,
            stored_name=invoice_filename,
            mime_type="application/pdf",
            file_size=invoice_path.stat().st_size,
            relative_path=relative_path,
            metadata={"invoice_number": invoice_number, "raffle_code": raffle_code},
        )

    summary["invoice"] = {
        "number": invoice_number,
        "relative_path": relative_path,
        "issued_at": (approved_at or datetime.now(timezone.utc)).isoformat(),
        "amount_cop": amount_cop,
        "reference": latest_order.get("reference") if latest_order else case.get("payment_reference"),
    }
    summary["customer_case"] = {
        "code": customer_case_code,
        "label": "Expediente HazloPorMi",
        "issued_at": (approved_at or datetime.now(timezone.utc)).isoformat(),
    }
    summary["raffle"] = {
        "code": raffle_code,
        "period": period_label,
        "status": "active",
    }
    updated = repository.update_case_status(case_id, status=case.get("estado") or "pagado_pendiente_intake", submission_summary=summary) or case
    if not updated.get("user_id") and updated.get("public_token"):
        updated = _persist_guest_ops(updated)
    repository.create_event(
        case_id=case_id,
        event_type="payment_artifacts_issued",
        actor_type="system",
        actor_id=None,
        payload={
            "customer_case_code": customer_case_code,
            "invoice_number": invoice_number,
            "raffle_code": raffle_code,
            "reference": summary["invoice"]["reference"],
        },
    )
    return updated


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.post("/public/analytics/event")
def capture_marketing_event(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = str(payload.get("session_id") or "").strip()
    event_name = str(payload.get("event_name") or "").strip().lower()
    if not session_id or not event_name:
        raise HTTPException(status_code=400, detail="session_id y event_name son obligatorios.")
    page_path = str(payload.get("page_path") or "").strip() or None
    source = str(payload.get("source") or "").strip() or None
    case_id = str(payload.get("case_id") or "").strip() or None
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    repository.create_marketing_event(
        session_id=session_id[:120],
        event_name=event_name[:80],
        page_path=page_path[:180] if page_path else None,
        source=source[:80] if source else None,
        case_id=case_id,
        metadata=metadata,
    )
    return {"ok": True}


@app.get("/public/marketing/config")
def public_marketing_config() -> dict[str, Any]:
    config = repository.get_marketing_config()
    return {
        "cta_variant": config.get("cta_variant") or "default",
        "cta_label": config.get("cta_label") or "Soluciona tu caso EPS y participa",
        "raffle_label": config.get("raffle_label") or "Rifa mayo: posibilidad de llevarse $2.500.000 COP",
        "updated_at": config.get("updated_at"),
    }


@app.get("/catalog/products", response_model=list[CatalogProductResponse])
def get_catalog_products() -> list[CatalogProductResponse]:
    return [CatalogProductResponse(**product) for product in list_catalog()]


@app.get("/catalog/entities", response_model=list[EntityAutocompleteResponse])
def get_catalog_entities(q: str, limit: int = 8) -> list[EntityAutocompleteResponse]:
    if len(q.strip()) < 2:
        return []
    entities = search_entity_directory(q, limit=max(1, min(limit, 12)))
    return [EntityAutocompleteResponse(**entity) for entity in entities]


@app.get("/public/files/{relative_path:path}")
def get_public_generated_file(relative_path: str) -> FileResponse:
    root = ensure_upload_root().resolve()
    file_path = absolute_path(relative_path).resolve()
    if root not in file_path.parents and file_path != root:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")
    return FileResponse(file_path)


@app.post("/public/leads/diagnosis", response_model=GuestDiagnosisResponse, status_code=status.HTTP_201_CREATED)
def create_guest_lead(payload: GuestLeadCreateRequest) -> GuestDiagnosisResponse:
    category = normalize_guest_category(payload.category)
    form_data = dict(payload.form_data or {})
    if payload.entity_name:
        form_data.setdefault("target_entity", payload.entity_name)
        form_data.setdefault("entity_name", payload.entity_name)
    if payload.urgency_level:
        form_data.setdefault("urgency_level", payload.urgency_level)

    result = analyzer.full_analysis(payload.description, category=category)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    result["facts"] = _merge_intake_into_facts(
        existing_facts=result["facts"],
        form_data=form_data,
        description=payload.description,
        category=category,
    )
    workflow = infer_workflow(
        category=category,
        description=payload.description,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        prior_actions=payload.prior_actions,
    )
    routing = build_routing(
        category=category,
        city=payload.city,
        department=payload.department,
        facts=result["facts"],
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
    )
    strategy = build_strategy_text(
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        legal_analysis=result["legal_analysis"],
        warnings=workflow["warnings"],
    )
    intake_review = validate_intake(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=payload.description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=payload.description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
        stage="preview",
    )
    document_rule_review = evaluate_document_rule(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        description=payload.description,
        facts=result["facts"],
    )
    result["facts"]["intake_review"] = intake_review
    result["facts"]["preview_gate"] = preview_gate
    result["facts"]["document_rule_review"] = document_rule_review
    result["facts"], result["legal_analysis"], routing = _enrich_architecture_outputs(
        category=category,
        description=payload.description,
        workflow=workflow,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        prior_actions=payload.prior_actions,
    )
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
        + result["facts"].get("dx_result", {}).get("blocking_reasons", [])
        + result["facts"].get("dx_result", {}).get("warnings", [])
    )
    public_token = build_public_token()
    summary = {
        "public_token": public_token,
        "customer_summary": {},
        "lead_source": "public_web",
    }
    case = repository.create_guest_case_record(
        public_token=public_token,
        user_name=payload.name,
        user_email=payload.email,
        user_phone=payload.phone,
        city=payload.city,
        department=payload.department,
        workflow_type=workflow["workflow_type"],
        category=category,
        description=payload.description,
        recommended_action=workflow["recommended_action"],
        strategy_text=strategy,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        routing=routing,
        prerequisites=workflow["prerequisites"],
        warnings=list(dict.fromkeys(combined_warnings)),
        submission_summary=summary,
    )
    customer_summary = build_customer_summary(case)
    case = repository.update_case_status(
        str(case["id"]),
        status="diagnosticado",
        submission_summary={**summary, "customer_summary": customer_summary},
    ) or case
    repository.create_event(
        case_id=str(case["id"]),
        event_type="guest_case_created",
        actor_type="guest",
        actor_id=None,
        payload={"category": category, "recommended_action": workflow["recommended_action"]},
    )
    return GuestDiagnosisResponse(
        case=_normalize_case(case),
        public_token=public_token,
        next_step="Completa el pago para desbloquear el formulario completo y la redaccion humana en hasta 24 horas habiles.",
        commercial_summary=customer_summary,
        price_cop=BASE_SERVICE_PRICE_COP,
    )


@app.get("/public/cases/{case_id}", response_model=GuestCaseStatusResponse)
def get_public_case_status(case_id: str, public_token: str) -> GuestCaseStatusResponse:
    case = _get_guest_case_or_404(case_id, public_token)
    return _guest_status_response(case)


@app.post("/public/cases/{case_id}/payments/wompi/session", response_model=GuestCheckoutSessionResponse)
def create_guest_wompi_checkout_session(
    case_id: str,
    payload: GuestCheckoutSessionRequest,
) -> GuestCheckoutSessionResponse:
    ensure_checkout_configured()
    case = _get_guest_case_or_404(case_id, payload.public_token)
    if case.get("payment_status") == "pagado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este caso ya tiene un pago aprobado.")
    amount_in_cents = amount_cop_to_cents(BASE_SERVICE_PRICE_COP)
    reference = build_reference(case_id, SERVICE_PRODUCT_CODE)
    checkout = build_checkout_payload(
        reference=reference,
        amount_in_cents=amount_in_cents,
        product_name=SERVICE_PRODUCT_NAME,
        description="Diagnostico, redaccion humana y guia detallada HazloPorMi en hasta 24 horas habiles.",
        customer_email=case["usuario_email"],
    )
    order = repository.create_payment_order(
        case_id=case_id,
        user_id=None,
        environment=settings.wompi_environment,
        product_code=SERVICE_PRODUCT_CODE,
        product_name=SERVICE_PRODUCT_NAME,
        include_filing=False,
        amount_cop=BASE_SERVICE_PRICE_COP,
        amount_in_cents=amount_in_cents,
        currency="COP",
        reference=reference,
        checkout_payload=checkout,
    )
    updated = repository.update_case_status(
        case_id,
        status="checkout_pendiente",
        submission_summary=_merge_submission_summary(case, checkout_reference=reference),
    ) or case
    repository.create_event(
        case_id=case_id,
        event_type="guest_payment_order_created",
        actor_type="guest",
        actor_id=None,
        payload={"reference": reference, "amount_cop": BASE_SERVICE_PRICE_COP},
    )
    return GuestCheckoutSessionResponse(public_token=payload.public_token, order=_normalize_payment_order(order), checkout=checkout)


@app.post("/public/payments/wompi/reconcile", response_model=GuestCaseStatusResponse)
def reconcile_guest_payment(payload: GuestPaymentReconcileRequest) -> GuestCaseStatusResponse:
    transaction = fetch_transaction(payload.transaction_id)
    result = _process_wompi_transaction_reconciliation(transaction, payload.reference)
    reference = result.reference or payload.reference
    if not reference:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible identificar la referencia del pago.")
    order = repository.get_payment_order_by_reference(reference)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")
    case = repository.get_case_by_id(str(order["case_id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Caso no encontrado.")
    if payload.public_token and str(case.get("public_token") or "") != payload.public_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este caso.")
    return _guest_status_response(case)


@app.post("/public/payments/simulate", response_model=GuestCaseStatusResponse)
def simulate_guest_payment(payload: GuestPaymentReconcileRequest) -> GuestCaseStatusResponse:
    if not payload.reference:
        raise HTTPException(status_code=400, detail="Falta reference")
    order = repository.get_payment_order_by_reference(payload.reference)
    if not order:
        raise HTTPException(status_code=404, detail="Pago no encontrado.")
    case = repository.get_case_by_id(str(order["case_id"]))
    if not case:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
    if payload.public_token and str(case.get("public_token") or "") != payload.public_token:
        raise HTTPException(status_code=403, detail="No tienes acceso a este caso.")
    
    # Only allow for QA emails
    email = str(case.get("usuario_email") or "").strip().lower()
    if email not in settings.qa_test_emails:
        raise HTTPException(status_code=403, detail="Simulacion no permitida para este correo.")
        
    repository.update_payment_order_status(
        payload.reference,
        status="APPROVED",
        provider_transaction_id=payload.transaction_id,
        provider_status="APPROVED",
        approved_at=datetime.now(timezone.utc),
    )
    updated_case = repository.update_case_payment(str(case["id"]), payload.reference, payment_status="pagado") or case
    updated_case = _ensure_payment_artifacts(str(case["id"])) or updated_case
    repository.create_event(
        case_id=str(case["id"]),
        event_type="payment_approved_simulated",
        actor_type="system",
        actor_id=None,
        payload={"reference": payload.reference},
    )
    updated_case = _persist_guest_ops(updated_case)
    return _guest_status_response(updated_case)


@app.patch("/public/cases/{case_id}/intake", response_model=GuestCaseStatusResponse)
def update_public_case_intake(case_id: str, payload: GuestIntakeUpdateRequest) -> GuestCaseStatusResponse:
    case = _get_guest_case_or_404(case_id, payload.public_token)
    if case.get("payment_status") != "pagado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Primero debes completar el pago.")

    category = normalize_guest_category(case.get("categoria") or case.get("category") or "")
    prior_actions = [item["id"] for item in (case.get("prerequisites") or []) if item.get("completed")]
    attachment_records = repository.list_files_for_case(case_id)
    attachment_context = build_attachment_context(attachment_records)
    enriched_description = enrich_description_with_attachment_context(payload.description, attachment_context)
    enriched_form_data = _merge_form_with_attachment_suggestions(
        form_data=payload.form_data or {},
        description=enriched_description,
        category=category,
        attachment_context=attachment_context,
    )
    facts = _merge_intake_into_facts(
        existing_facts=case.get("facts") or {},
        form_data=enriched_form_data,
        description=enriched_description,
        category=category,
    )
    legal_analysis = case.get("legal_analysis") or {}
    workflow = infer_workflow(
        category=category,
        description=enriched_description,
        facts=facts,
        legal_analysis=legal_analysis,
        prior_actions=prior_actions,
    )
    routing = build_routing(
        category=category,
        city=payload.city,
        department=payload.department,
        facts=facts,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
    )
    strategy = build_strategy_text(
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        legal_analysis=legal_analysis,
        warnings=workflow["warnings"],
    )
    intake_review = validate_intake(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=facts,
        prior_actions=prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=facts,
        prior_actions=prior_actions,
        stage="save",
    )
    document_rule_review = evaluate_document_rule(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=facts,
    )
    facts["intake_review"] = intake_review
    facts["preview_gate"] = preview_gate
    facts["document_rule_review"] = document_rule_review
    facts["attachment_intelligence"] = attachment_context
    facts["autofill_suggestions"] = enriched_form_data.get("_autofill") or {}
    facts, legal_analysis, routing = _enrich_architecture_outputs(
        category=category,
        description=enriched_description,
        workflow=workflow,
        facts=facts,
        legal_analysis=legal_analysis,
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        prior_actions=prior_actions,
    )
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
        + facts.get("dx_result", {}).get("blocking_reasons", [])
        + facts.get("dx_result", {}).get("warnings", [])
    )
    case_for_summary = {**case, "categoria": category, "recommended_action": workflow["recommended_action"], "facts": facts}
    customer_guide = build_customer_guide(case_for_summary)
    operational_brief = build_operational_brief(case_for_summary)
    delivery_package = build_delivery_package(case_for_summary)
    sla_deadline_at = compute_sla_deadline().isoformat()
    submission_summary = _merge_submission_summary(
        case,
        public_token=payload.public_token,
        customer_summary=build_customer_summary(case_for_summary),
        customer_guide=customer_guide,
        operational_brief=operational_brief,
        delivery_package=delivery_package,
        sla_deadline_at=sla_deadline_at,
    )
    updated = repository.update_guest_case_intake(
        case_id,
        user_name=payload.name,
        user_email=payload.email,
        user_document=payload.document_number,
        user_phone=payload.phone,
        city=payload.city,
        department=payload.department,
        address=payload.address,
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=facts,
        legal_analysis=legal_analysis,
        routing=routing,
        prerequisites=workflow["prerequisites"],
        warnings=list(dict.fromkeys(combined_warnings)),
        recommended_action=workflow["recommended_action"],
        strategy_text=strategy,
        submission_summary=submission_summary,
        status="pagado_en_revision",
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible actualizar el caso.")
    updated = _persist_guest_ops(updated)
    repository.create_event(
        case_id=case_id,
        event_type="guest_intake_completed",
        actor_type="guest",
        actor_id=None,
        payload={"sla_deadline_at": sla_deadline_at, "recommended_action": workflow["recommended_action"]},
    )
    return _guest_status_response(updated)


@app.post("/public/cases/{case_id}/uploads", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_public_case_file(
    case_id: str,
    public_token: str = Form(...),
    file: UploadFile = File(...),
    file_kind: str = Form(default="attachment"),
) -> UploadedFileResponse:
    case = _get_guest_case_or_404(case_id, public_token)
    if case.get("payment_status") != "pagado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Primero debes completar el pago.")
    saved = save_upload(file, bucket="cases", owner_id=str(case["id"]))
    record = repository.create_case_file(case_id=case_id, uploaded_by=None, file_kind=file_kind, **saved)
    repository.create_event(
        case_id=case_id,
        event_type="guest_attachment_added",
        actor_type="guest",
        actor_id=None,
        payload={"file_id": str(record["id"]), "name": record["original_name"]},
    )
    return _normalize_file(record)


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> AuthResponse:
    email = _normalize_email_input(payload.email)
    existing = repository.get_user_by_email(email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese correo ya está registrado.")

    role = _role_for_email(email)
    user = repository.create_user(payload.name, email, hash_password(payload.password), role=role)
    token = create_token(str(user["id"]), user["email"], settings.jwt_secret)
    return AuthResponse(token=token, user=_normalize_user(user))


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response) -> AuthResponse:
    email = _normalize_email_input(payload.email)
    client_ip = (request.client.host if request.client else "unknown").strip() or "unknown"
    limit_key = f"{client_ip}:{email.lower()}"
    now = time.time()
    attempts = [ts for ts in _FAILED_LOGIN_ATTEMPTS.get(limit_key, []) if now - ts < _LOGIN_LIMIT_WINDOW_SECONDS]
    _FAILED_LOGIN_ATTEMPTS[limit_key] = attempts
    if len(attempts) >= _LOGIN_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos de acceso. Intenta de nuevo en 15 minutos.",
        )

    user = repository.get_user_by_email(email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        attempts.append(now)
        _FAILED_LOGIN_ATTEMPTS[limit_key] = attempts
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas.")

    expected_role = _role_for_email(user.get("email") or email)
    if user.get("role") != expected_role:
        refreshed = repository.update_user_role(str(user["id"]), expected_role)
        if refreshed:
            user = {**user, **refreshed}

    if user.get("role") == "internal" and bool(user.get("totp_enabled")):
        if not (payload.otp_code or payload.recovery_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "2fa_required", "message": "Ingresa tu codigo de Microsoft Authenticator o un codigo de recuperacion."},
            )
        if not _verify_internal_second_factor(user, otp_code=payload.otp_code, recovery_code=payload.recovery_code):
            attempts.append(now)
            _FAILED_LOGIN_ATTEMPTS[limit_key] = attempts
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "2fa_invalid", "message": "El codigo de verificacion no es valido."},
            )

    _FAILED_LOGIN_ATTEMPTS.pop(limit_key, None)
    token = create_token(str(user["id"]), user["email"], settings.jwt_secret)
    if user.get("role") == "internal":
        response.set_cookie(
            key="admin_session",
            value=token,
            httponly=True,
            secure=settings.app_env.lower() == "production",
            samesite="lax",
            max_age=7 * 24 * 3600,
            path="/",
        )
    return AuthResponse(token=token, user=_normalize_user(user))


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    return _normalize_user(current_user)


@app.post("/auth/2fa/setup", response_model=TwoFactorSetupResponse)
def setup_two_factor(current_user: dict[str, Any] = Depends(get_internal_user)) -> TwoFactorSetupResponse:
    secret = generate_totp_secret()
    issuer = _totp_issuer()
    account_label = str(current_user.get("email") or "")
    return TwoFactorSetupResponse(
        secret=secret,
        manual_entry_key=secret,
        otpauth_uri=build_otpauth_uri(secret=secret, account_name=account_label, issuer=issuer),
        issuer=issuer,
        account_label=account_label,
    )


@app.post("/auth/2fa/enable", response_model=TwoFactorEnableResponse)
def enable_two_factor(
    payload: TwoFactorEnableRequest,
    current_user: dict[str, Any] = Depends(get_internal_user),
) -> TwoFactorEnableResponse:
    secret = str(payload.secret or "").strip().replace(" ", "").upper()
    if not verify_totp_code(secret, payload.otp_code):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El codigo TOTP no es valido.")

    recovery_codes = generate_recovery_codes()
    updated = repository.enable_user_totp(
        str(current_user["id"]),
        secret=secret,
        recovery_hashes=[hash_recovery_code(code) for code in recovery_codes],
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return TwoFactorEnableResponse(ok=True, user=_normalize_user(updated), recovery_codes=recovery_codes)


@app.post("/auth/2fa/disable", response_model=UserResponse)
def disable_two_factor(
    payload: TwoFactorDisableRequest,
    current_user: dict[str, Any] = Depends(get_internal_user),
) -> UserResponse:
    full_user = repository.get_user_by_email(str(current_user.get("email") or ""))
    if not full_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    if bool(full_user.get("totp_enabled")) and not _verify_internal_second_factor(
        full_user,
        otp_code=payload.otp_code,
        recovery_code=payload.recovery_code,
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes confirmar con un codigo valido para desactivar 2FA.")

    updated = repository.disable_user_totp(str(current_user["id"]))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return _normalize_user(updated)


@app.post("/auth/logout")
def logout(response: Response) -> dict[str, str]:
    response.delete_cookie(key="admin_session", path="/")
    return {"status": "ok"}


@app.patch("/auth/me", response_model=UserResponse)
def update_profile(
    payload: UserProfileUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    updated = repository.update_user_profile(
        str(current_user["id"]),
        name=payload.name,
        document_number=payload.document_number,
        phone=payload.phone,
        city=payload.city,
        department=payload.department,
        address=payload.address,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return _normalize_user(updated)


@app.post("/uploads", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_temp_file(
    file: UploadFile = File(...),
    file_kind: str = Form(default="attachment"),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UploadedFileResponse:
    saved = save_upload(file, bucket="temp", owner_id=str(current_user["id"]))
    record = repository.create_temp_file(uploaded_by=str(current_user["id"]), file_kind=file_kind, **saved)
    return _normalize_file(record)


@app.post("/analysis/preview", response_model=AnalysisPreviewResponse)
def analysis_preview(
    payload: AnalysisPreviewRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> AnalysisPreviewResponse:
    attachment_records: list[dict[str, Any]] = []
    for file_id in payload.attachment_ids:
        file_record = repository.get_file_by_id(file_id)
        if not file_record:
            continue
        if str(file_record.get("uploaded_by")) != str(current_user["id"]):
            continue
        attachment_records.append(file_record)

    attachment_context = build_attachment_context(attachment_records)
    enriched_description = enrich_description_with_attachment_context(payload.description, attachment_context)
    enriched_form_data = _merge_form_with_attachment_suggestions(
        form_data=payload.form_data or {},
        description=enriched_description,
        category=payload.category,
        attachment_context=attachment_context,
    )

    result = analyzer.full_analysis(enriched_description, category=payload.category)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    result["facts"] = _merge_intake_into_facts(
        existing_facts=result["facts"],
        form_data=enriched_form_data,
        description=enriched_description,
        category=payload.category,
    )

    workflow = infer_workflow(
        category=payload.category,
        description=enriched_description,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        prior_actions=payload.prior_actions,
    )
    routing = build_routing(
        category=payload.category,
        city=payload.city,
        department=payload.department,
        facts=result["facts"],
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
    )
    strategy = build_strategy_text(
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        legal_analysis=result["legal_analysis"],
        warnings=workflow["warnings"],
    )
    intake_review = validate_intake(
        category=payload.category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=payload.category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
        stage="preview",
    )
    document_rule_review = evaluate_document_rule(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=result["facts"],
    )
    result["facts"]["intake_review"] = intake_review
    result["facts"]["preview_gate"] = preview_gate
    result["facts"]["document_rule_review"] = document_rule_review
    result["facts"]["attachment_intelligence"] = attachment_context
    result["facts"]["autofill_suggestions"] = enriched_form_data.get("_autofill") or {}
    result["facts"], result["legal_analysis"], routing = _enrich_architecture_outputs(
        category=payload.category,
        description=enriched_description,
        workflow=workflow,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        prior_actions=payload.prior_actions,
    )
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
        + result["facts"].get("dx_result", {}).get("blocking_reasons", [])
        + result["facts"].get("dx_result", {}).get("warnings", [])
    )
    return AnalysisPreviewResponse(
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        strategy=strategy,
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        prerequisites=workflow["prerequisites"],
        warnings=list(dict.fromkeys(combined_warnings)),
        routing=routing,
        dx_result=result["facts"].get("dx_result") or {},
        pending_questions=result["facts"].get("pending_questions") or [],
        case_route=(routing or {}).get("case_route"),
        tutela_procedencia=result["facts"].get("tutela_procedencia") or {},
        source_validation_policy=result["facts"].get("source_validation_policy") or {},
        layer_outputs=result["facts"].get("layer_outputs") or {},
    )


@app.post("/cases", response_model=CaseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreateRequest, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDetailResponse:
    _require_profile(current_user)

    attachment_records: list[dict[str, Any]] = []
    for file_id in payload.attachment_ids:
        file_record = repository.get_file_by_id(file_id)
        if not file_record:
            continue
        if str(file_record.get("uploaded_by")) != str(current_user["id"]):
            continue
        attachment_records.append(file_record)

    attachment_context = build_attachment_context(attachment_records)
    enriched_description = enrich_description_with_attachment_context(payload.description, attachment_context)
    enriched_form_data = _merge_form_with_attachment_suggestions(
        form_data=payload.form_data or {},
        description=enriched_description,
        category=payload.category,
        attachment_context=attachment_context,
    )

    result = analyzer.full_analysis(enriched_description, category=payload.category)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    result["facts"] = _merge_intake_into_facts(
        existing_facts=result["facts"],
        form_data=enriched_form_data,
        description=enriched_description,
        category=payload.category,
    )

    workflow = infer_workflow(
        category=payload.category,
        description=enriched_description,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        prior_actions=payload.prior_actions,
    )
    routing = build_routing(
        category=payload.category,
        city=payload.city,
        department=payload.department,
        facts=result["facts"],
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
    )
    strategy = build_strategy_text(
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        legal_analysis=result["legal_analysis"],
        warnings=workflow["warnings"],
    )
    intake_review = validate_intake(
        category=payload.category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=payload.category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
        stage="preview",
    )
    document_rule_review = evaluate_document_rule(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=result["facts"],
    )
    result["facts"]["intake_review"] = intake_review
    result["facts"]["preview_gate"] = preview_gate
    result["facts"]["document_rule_review"] = document_rule_review
    result["facts"]["attachment_intelligence"] = attachment_context
    result["facts"]["autofill_suggestions"] = enriched_form_data.get("_autofill") or {}
    result["facts"], result["legal_analysis"], routing = _enrich_architecture_outputs(
        category=payload.category,
        description=enriched_description,
        workflow=workflow,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        prior_actions=payload.prior_actions,
    )
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
        + result["facts"].get("dx_result", {}).get("blocking_reasons", [])
        + result["facts"].get("dx_result", {}).get("warnings", [])
    )
    case = repository.create_case_record(
        user_id=str(current_user["id"]),
        user_name=current_user["name"],
        user_email=current_user["email"],
        user_document=current_user["document_number"],
        user_phone=current_user["phone"],
        city=payload.city,
        department=payload.department,
        address=current_user["address"],
        workflow_type=workflow["workflow_type"],
        category=payload.category,
        description=enriched_description,
        recommended_action=workflow["recommended_action"],
        strategy_text=strategy,
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        routing=routing,
        prerequisites=workflow["prerequisites"],
        warnings=list(dict.fromkeys(combined_warnings)),
        attachment_ids=payload.attachment_ids,
    )
    if payload.attachment_ids:
        attached = repository.attach_files_to_case(str(case["id"]), str(current_user["id"]), payload.attachment_ids)
        for item in attached:
            updated_path = move_relative_path(item["relative_path"], bucket="cases", owner_id=str(case["id"]))
            repository.update_file_location(str(item["id"]), case_id=str(case["id"]), relative_path=updated_path)
            repository.create_event(
                case_id=str(case["id"]),
                event_type="attachment_added",
                actor_type="user",
                actor_id=str(current_user["id"]),
                payload={"file_id": str(item["id"]), "name": item["original_name"], "path": updated_path},
            )
    repository.create_event(
        case_id=str(case["id"]),
        event_type="case_created",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={
            "workflow_type": workflow["workflow_type"],
            "recommended_action": workflow["recommended_action"],
            "case_route": routing.get("case_route"),
            "viability": (result["facts"].get("dx_result") or {}).get("viability_preliminary"),
        },
    )
    return _snapshot_case_detail(_rehydrate_case_intelligence(case))


@app.get("/cases", response_model=list[CaseResponse])
def list_cases(current_user: dict[str, Any] = Depends(get_current_user)) -> list[CaseResponse]:
    cases = repository.list_cases_for_user(str(current_user["id"]))
    return [_normalize_case(_reconcile_case_payment(case)) for case in cases]


@app.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    return _snapshot_case_detail(case)


@app.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> Response:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="TrÃ¡mite no encontrado.")
    deleted = repository.delete_case_for_user(case_id, str(current_user["id"]))
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible eliminar el trÃ¡mite.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.patch("/cases/{case_id}/intake", response_model=CaseDetailResponse)
def update_case_intake(
    case_id: str,
    payload: CaseIntakeUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    category = case.get("categoria") or case.get("category")
    prior_actions = [item["id"] for item in (case.get("prerequisites") or []) if item.get("completed")]
    attachment_records = repository.list_files_for_case(case_id)
    attachment_context = build_attachment_context(attachment_records)
    enriched_description = enrich_description_with_attachment_context(payload.description, attachment_context)
    enriched_form_data = _merge_form_with_attachment_suggestions(
        form_data=payload.form_data or {},
        description=enriched_description,
        category=category,
        attachment_context=attachment_context,
    )
    facts = _merge_intake_into_facts(
        existing_facts=case.get("facts") or {},
        form_data=enriched_form_data,
        description=enriched_description,
        category=category,
    )
    legal_analysis = case.get("legal_analysis") or {}
    workflow = infer_workflow(
        category=category,
        description=enriched_description,
        facts=facts,
        legal_analysis=legal_analysis,
        prior_actions=prior_actions,
    )
    routing = build_routing(
        category=category,
        city=case.get("usuario_ciudad") or current_user.get("city") or "",
        department=case.get("usuario_departamento") or current_user.get("department") or "",
        facts=facts,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
    )
    strategy = build_strategy_text(
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        legal_analysis=legal_analysis,
        warnings=workflow["warnings"],
    )
    intake_review = validate_intake(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=facts,
        prior_actions=prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=category,
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=enriched_description,
        facts=facts,
        prior_actions=prior_actions,
        stage="save",
    )
    document_rule_review = evaluate_document_rule(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=facts,
    )
    facts["intake_review"] = intake_review
    facts["preview_gate"] = preview_gate
    facts["document_rule_review"] = document_rule_review
    facts["attachment_intelligence"] = attachment_context
    facts["autofill_suggestions"] = enriched_form_data.get("_autofill") or {}
    facts, legal_analysis, routing = _enrich_architecture_outputs(
        category=category,
        description=enriched_description,
        workflow=workflow,
        facts=facts,
        legal_analysis=legal_analysis,
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        prior_actions=prior_actions,
    )
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
        + facts.get("dx_result", {}).get("blocking_reasons", [])
        + facts.get("dx_result", {}).get("warnings", [])
    )
    updated = repository.update_case_intake(
        case_id,
        workflow_type=workflow["workflow_type"],
        description=enriched_description,
        facts=facts,
        legal_analysis=legal_analysis,
        routing=routing,
        prerequisites=workflow["prerequisites"],
        warnings=list(dict.fromkeys(combined_warnings)),
        recommended_action=workflow["recommended_action"],
        strategy_text=strategy,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible actualizar el expediente.")

    repository.create_event(
        case_id=case_id,
        event_type="case_intake_updated",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={
            "description_length": len(enriched_description),
            "fields": sorted(key for key in (enriched_form_data or {}).keys() if not key.startswith("_")),
            "case_route": routing.get("case_route"),
            "viability": (facts.get("dx_result") or {}).get("viability_preliminary"),
        },
    )
    return _snapshot_case_detail(updated)


@app.get("/cases/{case_id}/timeline", response_model=CaseDetailResponse)
def get_case_timeline(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    return _snapshot_case_detail(case)


@app.post("/cases/{case_id}/payment", response_model=CaseResponse)
def confirm_payment(
    case_id: str,
    payload: PaymentConfirmationRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    updated = repository.update_case_payment(case_id, payload.reference)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible registrar el pago.")
    updated = _ensure_payment_artifacts(case_id) or updated

    repository.create_event(
        case_id=case_id,
        event_type="payment_confirmed",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={"reference": payload.reference},
    )
    return _normalize_case(updated)


@app.post("/cases/{case_id}/payment/test", response_model=CaseResponse)
def confirm_test_payment(
    case_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    if not _is_qa_test_user(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Este pago de prueba no está habilitado para tu cuenta.")

    reference = f"QA-{str(case_id).upper()[:8]}-{datetime.now(timezone.utc).strftime('%H%M%S')}"
    updated = repository.update_case_payment(case_id, reference)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible registrar el pago de prueba.")
    updated = _ensure_payment_artifacts(case_id) or updated

    repository.create_event(
        case_id=case_id,
        event_type="payment_confirmed_test",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={"reference": reference, "mode": "qa_test"},
    )
    return _normalize_case(updated)


@app.post("/cases/{case_id}/payments/wompi/session", response_model=WompiCheckoutSessionResponse)
def create_wompi_checkout_session(
    case_id: str,
    payload: WompiCheckoutSessionRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> WompiCheckoutSessionResponse:
    ensure_checkout_configured()

    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    if case.get("payment_status") == "pagado" and not payload.add_on_type:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este trámite ya tiene el pago base aprobado.")

    if case.get("payment_status") == "pagado":
        add_on_type = _lower(payload.add_on_type)
        config = ADDON_ORDER_CONFIG.get(add_on_type)
        if not config:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fue posible determinar el adicional a cobrar.")
        product_code = config["code"]
        product_name = config["name"]
        include_filing = add_on_type in {"filing_auto", "filing_bundle"}
        amount_cop = ADDON_PRICES_COP[add_on_type]
        amount_in_cents = amount_cop_to_cents(amount_cop)
        reference = build_reference(case_id, product_code)
        description = config["description"]
    else:
        product_code = payload.product_code or suggest_product_code(case.get("recommended_action"))
        product = get_product(product_code or "")
        if not product:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fue posible determinar el producto a cobrar.")

        amount_cop = product.price_with_filing_cop if payload.include_filing else product.price_cop
        amount_in_cents = amount_cop_to_cents(amount_cop)
        reference = build_reference(case_id, product.code)
        product_name = product.name if not payload.include_filing else f"{product.name} + radicacion"
        product_code = product.code
        include_filing = payload.include_filing
        description = product.short_description
    checkout = build_checkout_payload(
        reference=reference,
        amount_in_cents=amount_in_cents,
        product_name=product_name,
        description=description,
        customer_email=current_user["email"],
    )
    order = repository.create_payment_order(
        case_id=case_id,
        user_id=str(current_user["id"]),
        environment=settings.wompi_environment,
        product_code=product_code,
        product_name=product_name,
        include_filing=include_filing,
        amount_cop=amount_cop,
        amount_in_cents=amount_in_cents,
        currency="COP",
        reference=reference,
        checkout_payload=checkout,
    )
    repository.create_event(
        case_id=case_id,
        event_type="payment_order_created",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={
            "reference": reference,
            "product_code": product_code,
            "product_name": product_name,
            "include_filing": include_filing,
            "add_on_type": payload.add_on_type,
            "amount_cop": amount_cop,
        },
    )
    return WompiCheckoutSessionResponse(order=_normalize_payment_order(order), checkout=checkout)


@app.get("/payments/{reference}", response_model=PaymentOrderResponse)
def get_payment(reference: str, current_user: dict[str, Any] = Depends(get_current_user)) -> PaymentOrderResponse:
    order = repository.get_payment_order_by_reference(reference)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado.")
    if str(order["user_id"]) != str(current_user["id"]) and not _is_internal(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este pago.")
    return _normalize_payment_order(order)


@app.post("/cases/{case_id}/document", response_model=CaseDocumentResponse)
def generate_document(
    case_id: str,
    payload: DocumentGenerateRequest | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseDocumentResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    if case.get("payment_status") != "pagado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes registrar el pago antes de generar el documento.")

    facts = dict(case.get("facts") or {})
    intake_form = dict(facts.get("intake_form") or {})
    if payload:
        if payload.regeneration_reason:
            intake_form["regeneration_reason"] = payload.regeneration_reason.strip()
        if payload.additional_context:
            intake_form["regeneration_additional_context"] = payload.additional_context.strip()
        facts["intake_form"] = intake_form
    case["facts"] = facts
    case = _rehydrate_case_intelligence(case)
    case = _refresh_verified_case_context(case)
    facts = dict(case.get("facts") or {})
    intake_form = dict(facts.get("intake_form") or {})
    attachment_records = repository.list_files_for_case(case_id)
    facts["uploaded_evidence_files"] = [
        {
            "id": str(item.get("id")),
            "original_name": str(item.get("original_name") or ""),
            "file_kind": str(item.get("file_kind") or ""),
            "relative_path": str(item.get("relative_path") or ""),
            "mime_type": str(item.get("mime_type") or ""),
            "file_size": int(item.get("file_size") or 0),
        }
        for item in attachment_records
        if item.get("original_name")
    ]
    facts["document_insights"] = analyzer.compose_document_insights(
        description=case.get("descripcion") or "",
        category=case.get("categoria") or case.get("category"),
        facts=facts,
        legal_analysis=case.get("legal_analysis") or {},
        intake_form=intake_form,
    )
    refreshed_agent_state = build_health_agent_state(
        category=case.get("categoria") or case.get("category") or "",
        workflow_type=case.get("workflow_type") or "",
        recommended_action=case.get("recommended_action") or "",
        description=case.get("descripcion") or "",
        facts=facts,
    )
    if refreshed_agent_state:
        facts["agent_state"] = refreshed_agent_state
    case["facts"] = facts
    generation_gate = validate_submission_readiness(
        category=case.get("categoria") or case.get("category") or "",
        workflow_type=case.get("workflow_type") or "",
        recommended_action=case.get("recommended_action") or "",
        description=case.get("descripcion") or "",
        facts=facts,
        prior_actions=[item["id"] for item in (case.get("prerequisites") or []) if item.get("completed")],
        stage="generate",
    )
    if generation_gate.get("blocking_issues"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_format_blocking_detail_with_actions(
                prefix="Todavia faltan datos minimos para generar este documento: ",
                blocking_issues=list(generation_gate.get("blocking_issues") or []),
                recommended_action=case.get("recommended_action") or "",
            ),
        )
    document_rule_review = evaluate_document_rule(
        recommended_action=case.get("recommended_action"),
        workflow_type=case.get("workflow_type"),
        description=case.get("descripcion") or "",
        facts=facts,
    )
    document_rule_review["blocking_issues"] = relax_health_tutela_blockers(
        list(document_rule_review.get("blocking_issues") or []),
        facts,
    )
    if document_rule_review.get("blocking_issues"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_format_blocking_detail_with_actions(
                prefix="Todavia faltan datos minimos para generar este documento: ",
                blocking_issues=list(document_rule_review.get("blocking_issues") or []),
                recommended_action=case.get("recommended_action") or "",
            ),
        )
    document, draft_trace = build_document_with_trace(case)
    quality_review = evaluate_generated_document(case, document)
    quality_review["blocking_issues"] = relax_health_tutela_blockers(
        list(quality_review.get("blocking_issues") or []),
        facts,
    )
    quality_review["passed"] = bool(
        quality_review.get("score", 0) >= quality_review.get("threshold", 0)
        and not quality_review.get("blocking_issues")
    )
    final_validation = build_final_validation(case=case, document=document, quality_review=quality_review)
    if not quality_review.get("passed"):
        blocking_issues = list(quality_review.get("blocking_issues") or [])
        actionable_blocking = [issue for issue in blocking_issues if not _is_ai_owned_quality_issue(issue)]
        ai_owned_only = not actionable_blocking
        if ai_owned_only:
            quality_review["passed"] = True
            quality_review["warnings"] = list(
                dict.fromkeys(
                    [
                        *(quality_review.get("warnings") or []),
                        "La IA seguira reforzando internamente el sustento juridico y la version final antes de la entrega.",
                    ]
                )
            )
        repository.create_event(
            case_id=case_id,
            event_type="document_generation_blocked",
            actor_type="system",
            actor_id=None,
            payload={
                "score": quality_review.get("score"),
                "threshold": quality_review.get("threshold"),
                "blocking_issues": actionable_blocking or blocking_issues,
                "warnings": quality_review.get("warnings"),
            },
        )
        if not ai_owned_only:
            quality_follow_up_questions = _build_quality_follow_up_questions(actionable_blocking or blocking_issues)
            if quality_follow_up_questions:
                existing_pending = [item for item in (facts.get("pending_questions") or []) if isinstance(item, dict)]
                follow_up_ids = {str(item.get("id") or "").strip() for item in quality_follow_up_questions}
                facts["quality_follow_up_questions"] = quality_follow_up_questions
                facts["pending_questions"] = quality_follow_up_questions + [
                    item for item in existing_pending if str(item.get("id") or "").strip() not in follow_up_ids
                ]
                refreshed_agent_state = build_health_agent_state(
                    category=case.get("categoria") or case.get("category") or "",
                    workflow_type=case.get("workflow_type") or "",
                    recommended_action=case.get("recommended_action") or "",
                    description=case.get("descripcion") or "",
                    facts=facts,
                )
                if refreshed_agent_state:
                    facts["agent_state"] = refreshed_agent_state
                try:
                    repository.update_case_intake(
                        case_id,
                        workflow_type=case.get("workflow_type") or "",
                        description=case.get("descripcion") or "",
                        facts=facts,
                        legal_analysis=case.get("legal_analysis") or {},
                        routing=case.get("routing") or {},
                        prerequisites=case.get("prerequisites") or [],
                        warnings=case.get("warnings") or [],
                        recommended_action=case.get("recommended_action") or "",
                        strategy_text=case.get("strategy_text") or "",
                    )
                except Exception:
                    pass
            detail_parts = actionable_blocking or quality_review.get("warnings") or [
                "El borrador no alcanzo la calidad juridica minima.",
            ]
            safe_detail_parts = [
                "La IA esta reforzando internamente el sustento juridico y todavia no alcanza la calidad minima de entrega."
                if _is_ai_owned_quality_issue(item)
                else item
                for item in detail_parts
            ]
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"El borrador no alcanza el umbral minimo de calidad ({quality_review.get('score')}/"
                    f"{quality_review.get('threshold')}). " + " | ".join(safe_detail_parts)
                ),
            )
    if not final_validation.get("apto_para_entrega"):
        repository.create_event(
            case_id=case_id,
            event_type="document_delivery_validation_blocked",
            actor_type="system",
            actor_id=None,
            payload=final_validation,
        )
        detail_parts = final_validation.get("blocking_issues") or final_validation.get("warnings") or [
            "La validacion final exige mas datos antes de entregar el documento.",
        ]
        actionable_gaps = final_validation.get("actionable_gaps") or []
        actionable_text = []
        for item in actionable_gaps[:4]:
            label = str(item.get("label") or "Dato faltante").strip()
            where = str(item.get("where_to_fix") or "Completa datos del caso").strip()
            actionable_text.append(f"{label} (completalo en: {where})")
        if actionable_text:
            detail_parts = list(detail_parts) + ["Corrige ahora: " + " | ".join(actionable_text)]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La validacion final del documento detecto ajustes pendientes: " + " | ".join(detail_parts),
        )
    updated = repository.update_case_document(case_id, document)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible generar el documento.")
    merged_submission_summary = {
        **(updated.get("submission_summary") or {}),
        "document_quality": quality_review,
        "final_validation": final_validation,
        "draft_trace": draft_trace,
    }
    try:
        updated = repository.update_case_status(
            case_id,
            status=updated.get("estado") or "listo_para_envio",
            submission_summary=merged_submission_summary,
        ) or updated
    except Exception:
        updated["submission_summary"] = merged_submission_summary

    try:
        repository.create_event(
            case_id=case_id,
            event_type="document_generated",
            actor_type="system",
            actor_id=None,
            payload={
                "length": len(document),
                "score": quality_review.get("score"),
                "threshold": quality_review.get("threshold"),
                "draft_trace": draft_trace,
            },
        )
    except Exception:
        pass
    return CaseDocumentResponse(case=_normalize_case(updated), document=document, quality_review=quality_review)


@app.post("/cases/{case_id}/submit", response_model=CaseDetailResponse)
def submit_case(
    case_id: str,
    payload: CaseSubmitRequest,
    request: Request = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    if case.get("payment_status") != "pagado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes registrar el pago antes de radicar.")
    if not case.get("generated_document"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Genera el documento antes de radicar.")
    signature = _normalize_submission_signature(payload.signature, reviewed_document=payload.reviewed_document, request=request)
    submission_policy = get_submission_policy(case)
    payment_entitlements = _payment_entitlements_from_orders(repository.list_payment_orders_for_case(case_id))
    allowed_modes = submission_policy.get("allowed_modes") or ["auto", "manual_contact", "presencial"]
    if payload.mode not in allowed_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Este documento no admite ese modo de radicacion en la fase actual. "
                f"Modo recomendado: {submission_policy.get('preferred_mode') or 'manual_contact'}."
            ),
        )

    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}
    channel = primary.get("channel") or routing.get("channel") or "manual"
    destination_name = primary.get("name")
    destination_contact = primary.get("contact")
    is_judicial_destination = str(primary.get("type") or "").lower() == "juzgado"
    subject = routing.get("subject")
    cc_list = [case.get("usuario_email")] if case.get("usuario_email") else []

    if _is_qa_test_user(current_user):
        channel = "email"
        destination_name = "Correo de prueba QA"
        destination_contact = settings.qa_test_radicado_email
        is_judicial_destination = False
        subject = f"[PRUEBA QA] {subject or (case.get('recommended_action') or 'Documento juridico')}"

    if payload.mode in {"auto", "manual_contact"} and is_judicial_destination and not payload.judicial_destination_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Este envio apunta a un juzgado o correo real de reparto. "
                "Debes confirmar expresamente que verificaste el documento final y que autorizas enviar a un destino judicial real."
            ),
        )
    if payload.mode == "auto" and not payment_entitlements.get("filing_auto_paid"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Debes pagar el paquete de radicacion antes de ejecutar este envio.",
        )
    if payload.mode == "manual_contact" and not payment_entitlements.get("filing_guide_paid"):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Debes pagar el paquete activo de radicacion antes de usar esta opcion.",
        )

    status_value = "enviado"
    manual_contact = {}
    response_payload = {
        "mode": payload.mode,
        "notes": payload.notes,
        "signature": signature,
    }
    radicado = None
    signed_artifacts = create_signed_submission_artifacts(
        case_id=case_id,
        recommended_action=str(case.get("recommended_action") or case.get("workflow_type") or "documento"),
        document_text=str(case.get("generated_document") or ""),
        signature=signature,
        radicado=radicado,
    )
    signed_delivery_result: dict[str, Any] = {"status": "pending"}

    if payload.mode == "auto":
        if not submission_policy.get("auto_allowed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "La radicacion automatica no esta habilitada para este documento en salud. "
                    f"Usa {submission_policy.get('preferred_mode') or 'manual_contact'}."
                ),
            )
        if not routing.get("automatable") or not destination_contact:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este caso no tiene canal automático confiable.")
        if routing.get("genera_radicado"):
            status_value = "radicado"
            radicado = generate_radicado("RAD")
            signed_artifacts = create_signed_submission_artifacts(
                case_id=case_id,
                recommended_action=str(case.get("recommended_action") or case.get("workflow_type") or "documento"),
                document_text=str(case.get("generated_document") or ""),
                signature=signature,
                radicado=radicado,
            )
        if channel == "email" and destination_contact:
            signed_delivery_result = send_signed_submission_email(
                recipient=destination_contact,
                subject=subject or f"{case.get('recommended_action') or 'Documento juridico'} - {case.get('usuario_nombre') or ''}".strip(" -"),
                body_text=f"Se remite {case.get('recommended_action') or 'documento juridico'} firmado por {signature['full_name']} identificado con documento {signature['document_number']}.",
                body_html=f"<p>Se remite <strong>{case.get('recommended_action') or 'documento juridico'}</strong> firmado por {signature['full_name']} identificado con documento {signature['document_number']}.</p>",
                attachments=[
                    {"relative_path": signed_artifacts.get("docx_relative_path", ""), "filename": signed_artifacts.get("docx_filename", "documento_firmado.docx"), "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
                    {"relative_path": signed_artifacts.get("pdf_relative_path", ""), "filename": signed_artifacts.get("pdf_filename", "documento_firmado.pdf"), "mime_type": "application/pdf"},
                ],
            )
        attempt_status = "success"
    elif payload.mode == "manual_contact":
        if not payload.manual_contact:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes ingresar un contacto manual.")
        destination_contact = payload.manual_contact
        manual_contact = {"value": payload.manual_contact, "notes": payload.notes}
        channel = "email" if "@" in payload.manual_contact else "manual"
        status_value = "enviado" if "@" in payload.manual_contact else "requiere_accion_manual"
        if channel == "email":
            radicado = generate_radicado("RAD")
            signed_artifacts = create_signed_submission_artifacts(
                case_id=case_id,
                recommended_action=str(case.get("recommended_action") or case.get("workflow_type") or "documento"),
                document_text=str(case.get("generated_document") or ""),
                signature=signature,
                radicado=radicado,
            )
            signed_delivery_result = send_signed_submission_email(
                recipient=destination_contact,
                subject=subject or f"{case.get('recommended_action') or 'Documento juridico'} - {case.get('usuario_nombre') or ''}".strip(" -"),
                body_text=f"Se remite {case.get('recommended_action') or 'documento juridico'} firmado por {signature['full_name']} identificado con documento {signature['document_number']}.",
                body_html=f"<p>Se remite <strong>{case.get('recommended_action') or 'documento juridico'}</strong> firmado por {signature['full_name']} identificado con documento {signature['document_number']}.</p>",
                attachments=[
                    {"relative_path": signed_artifacts.get("docx_relative_path", ""), "filename": signed_artifacts.get("docx_filename", "documento_firmado.docx"), "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
                    {"relative_path": signed_artifacts.get("pdf_relative_path", ""), "filename": signed_artifacts.get("pdf_filename", "documento_firmado.pdf"), "mime_type": "application/pdf"},
                ],
            )
        attempt_status = "manual_contact"
    else:
        manual_contact = {"mode": "presencial", "notes": payload.notes, "signature": signature}
        status_value = "requiere_accion_manual"
        attempt_status = "presencial_required"
        response_payload["instructions"] = routing.get("fallback", {}).get("instructions") or []

    response_payload["signed_artifacts"] = signed_artifacts
    response_payload["delivery_result"] = signed_delivery_result

    repository.create_submission_attempt(
        case_id=case_id,
        channel=channel,
        destination_name=destination_name,
        destination_contact=destination_contact,
        subject=subject,
        cc=cc_list,
        status=attempt_status,
        radicado=radicado,
        response_payload=response_payload,
    )
    updated = repository.update_case_submission(
        case_id,
        status=status_value,
        manual_contact=manual_contact,
        submission_summary={
            "last_channel": channel,
            "last_destination": destination_name,
            "last_contact": destination_contact,
            "radicado": radicado,
            "sent_copy_to_user": True,
            "mode": payload.mode,
            "signature": signature,
            "signed_artifacts": signed_artifacts,
            "delivery_result": signed_delivery_result,
            "submission_policy": submission_policy,
            "guidance": build_submission_guidance(case=case, mode=payload.mode, channel=channel, radicado=radicado),
        },
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible actualizar el trámite.")

    guidance = (updated.get("submission_summary") or {}).get("guidance") or build_submission_guidance(
        case=updated,
        mode=payload.mode,
        channel=channel,
        radicado=radicado,
    )
    email_result = send_post_radicado_email(recipient=updated.get("usuario_email"), case=updated, guidance=guidance)
    whatsapp_result = send_post_radicado_whatsapp(phone=updated.get("usuario_telefono"), case=updated, guidance=guidance)
    updated = _apply_post_radicado_email_result(
        case_id=case_id,
        base_case=updated,
        current_status=updated.get("estado") or status_value,
        manual_contact=updated.get("manual_contact") or manual_contact,
        guidance=guidance,
        email_result=email_result,
        whatsapp_result=whatsapp_result,
    )

    repository.create_event(
        case_id=case_id,
        event_type="submission_attempted",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={"mode": payload.mode, "channel": channel, "radicado": radicado, "signature": signature, "delivery_result": signed_delivery_result},
    )
    return _snapshot_case_detail(updated)


@app.post("/cases/{case_id}/manual-radicado", response_model=CaseDetailResponse)
def register_manual_radicado(
    case_id: str,
    payload: ManualRadicadoRequest,
    request: Request = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tr?mite no encontrado.")
    if not case.get("generated_document"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Genera el documento antes de registrar el radicado.")

    signature = _normalize_submission_signature(payload.signature, reviewed_document=payload.reviewed_document, request=request)
    signed_artifacts = create_signed_submission_artifacts(
        case_id=case_id,
        recommended_action=str(case.get("recommended_action") or case.get("workflow_type") or "documento"),
        document_text=str(case.get("generated_document") or ""),
        signature=signature,
        radicado=payload.radicado,
    )

    repository.create_submission_attempt(
        case_id=case_id,
        channel="manual_record",
        destination_name=(case.get("routing") or {}).get("primary_target", {}).get("name"),
        destination_contact=(case.get("routing") or {}).get("primary_target", {}).get("contact"),
        subject=(case.get("routing") or {}).get("subject"),
        cc=[case.get("usuario_email")] if case.get("usuario_email") else [],
        status="manual_radicado",
        radicado=payload.radicado,
        response_payload={
            "notes": payload.notes,
            "signature": signature,
            "signed_artifacts": signed_artifacts,
        },
    )
    updated = repository.update_case_status(
        case_id,
        status="radicado",
        submission_summary={
            **(case.get("submission_summary") or {}),
            "radicado": payload.radicado,
            "manual_notes": payload.notes,
            "signature": signature,
            "signed_artifacts": signed_artifacts,
            "submission_policy": get_submission_policy(case),
            "guidance": build_submission_guidance(case=case, mode="manual_contact", channel="manual_record", radicado=payload.radicado),
        },
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible registrar el radicado.")

    guidance = (updated.get("submission_summary") or {}).get("guidance") or build_submission_guidance(
        case=updated,
        mode="manual_contact",
        channel="manual_record",
        radicado=payload.radicado,
    )
    email_result = send_post_radicado_email(recipient=updated.get("usuario_email"), case=updated, guidance=guidance)
    whatsapp_result = send_post_radicado_whatsapp(phone=updated.get("usuario_telefono"), case=updated, guidance=guidance)
    updated = _apply_post_radicado_email_result(
        case_id=case_id,
        base_case=updated,
        current_status=updated.get("estado") or "radicado",
        guidance=guidance,
        email_result=email_result,
        whatsapp_result=whatsapp_result,
    )

    repository.create_event(
        case_id=case_id,
        event_type="manual_radicado_recorded",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={
            "radicado": payload.radicado,
            "notes": payload.notes,
            "signature": signature,
            "signed_artifacts": signed_artifacts,
        },
    )
    return _snapshot_case_detail(updated)


@app.post("/cases/{case_id}/follow-up", response_model=CaseDetailResponse)
def report_case_follow_up(
    case_id: str,
    payload: FollowUpReportRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tramite no encontrado.")

    report_payload = {
        "note": payload.note,
        "source": payload.source,
        "received_at_label": payload.received_at_label,
        "reported_at": datetime.now(timezone.utc).isoformat(),
    }
    updated = repository.update_case_status(
        case_id,
        status=case.get("estado") or "seguimiento",
        submission_summary={
            **(case.get("submission_summary") or {}),
            "last_follow_up_report": report_payload,
        },
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible registrar la novedad.")

    repository.create_event(
        case_id=case_id,
        event_type="judicial_update_reported",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload=report_payload,
    )
    return _snapshot_case_detail(updated)


@app.post("/cases/{case_id}/evidence", response_model=UploadedFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_case_evidence(
    case_id: str,
    file: UploadFile = File(...),
    note: str = Form(default=""),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UploadedFileResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    saved = save_upload(file, bucket="cases", owner_id=case_id)
    duplicate = repository.find_duplicate_case_file(
        case_id=case_id,
        uploaded_by=str(current_user["id"]),
        original_name=str(saved["original_name"]),
        mime_type=str(saved["mime_type"]),
        file_size=int(saved["file_size"]),
    )
    if duplicate:
        duplicate_path = absolute_path(str(saved["relative_path"]))
        if duplicate_path.exists():
            duplicate_path.unlink(missing_ok=True)
        return _normalize_file(duplicate)

    record = repository.create_case_file(
        case_id=case_id,
        uploaded_by=str(current_user["id"]),
        file_kind="evidence",
        metadata={"note": note},
        **saved,
    )
    repository.create_event(
        case_id=case_id,
        event_type="evidence_uploaded",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={"file_id": str(record["id"]), "note": note},
    )
    _rehydrate_case_intelligence(case)
    return _normalize_file(record)


@app.get("/files/{file_id}")
def download_file(file_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> FileResponse:
    file_record = repository.get_file_by_id(file_id)
    if not file_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo no encontrado.")

    case_id = file_record.get("case_id")
    if case_id:
        case = repository.get_case_by_id(str(case_id))
        if not case:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expediente no encontrado.")
        if str(case.get("user_id")) != str(current_user["id"]) and not _is_internal(current_user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este archivo.")
    elif str(file_record.get("uploaded_by")) != str(current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este archivo.")

    path = absolute_path(file_record["relative_path"])
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo físico no encontrado.")
    return FileResponse(Path(path), filename=file_record["original_name"], media_type=file_record["mime_type"])


def _wompi_case_payment_status(provider_status: str) -> str:
    mapping = {
        "APPROVED": "pagado",
        "DECLINED": "rechazado",
        "ERROR": "error",
        "VOIDED": "anulado",
        "PENDING": "pendiente",
    }
    return mapping.get(provider_status, "pendiente")


def _wompi_order_status(provider_status: str) -> str:
    mapping = {
        "APPROVED": "approved",
        "DECLINED": "declined",
        "ERROR": "error",
        "VOIDED": "voided",
        "PENDING": "pending",
    }
    return mapping.get(provider_status, "pending")


def _validate_wompi_transaction_against_order(transaction: dict[str, Any], order: dict[str, Any]) -> None:
    tx_currency = str(transaction.get("currency") or "").upper()
    order_currency = str(order.get("currency") or "").upper()
    if tx_currency and order_currency and tx_currency != order_currency:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Moneda de transaccion no coincide.")

    tx_amount = transaction.get("amount_in_cents")
    order_amount = order.get("amount_in_cents")
    try:
        tx_amount_int = int(tx_amount) if tx_amount is not None else None
        order_amount_int = int(order_amount) if order_amount is not None else None
    except (TypeError, ValueError):
        tx_amount_int = None
        order_amount_int = None
    if tx_amount_int is not None and order_amount_int is not None and tx_amount_int != order_amount_int:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Monto de transaccion no coincide.")


def _process_wompi_webhook(event_payload: dict[str, Any]) -> WompiWebhookResponse:
    ensure_webhook_configured()
    if not verify_event_signature(event_payload, settings.wompi_event_secret):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Firma de evento Wompi inválida.")

    transaction = extract_transaction_from_event(event_payload)
    reference = transaction.get("reference")
    provider_status = str(transaction.get("status") or "PENDING").upper()
    if not reference:
        return WompiWebhookResponse(ok=True, processed=False, status=_wompi_order_status(provider_status))

    existing = repository.get_payment_order_by_reference(str(reference))
    if not existing:
        return WompiWebhookResponse(ok=True, processed=False, reference=str(reference), status=_wompi_order_status(provider_status))
    _validate_wompi_transaction_against_order(transaction, existing)

    next_order_status = _wompi_order_status(provider_status)
    approved_at = parse_approved_at(transaction) if provider_status == "APPROVED" else None
    updated_order = repository.update_payment_order_status(
        str(reference),
        status=next_order_status,
        provider_transaction_id=str(transaction.get("id")) if transaction.get("id") else None,
        provider_status=provider_status,
        webhook_payload=event_payload,
        approved_at=approved_at,
    )
    if not updated_order:
        return WompiWebhookResponse(ok=True, processed=False, reference=str(reference), status=next_order_status)

    case_record = repository.get_case_by_id(str(existing["case_id"]))
    if case_record and (case_record.get("payment_status") != "pagado" or provider_status == "APPROVED"):
        repository.update_case_payment(
            str(existing["case_id"]),
            str(reference),
            payment_status=_wompi_case_payment_status(provider_status),
        )
        if provider_status == "APPROVED":
            _ensure_payment_artifacts(str(existing["case_id"]))

    if existing.get("status") != next_order_status:
        repository.create_event(
            case_id=str(existing["case_id"]),
            event_type="payment_webhook_updated",
            actor_type="system",
            actor_id=None,
            payload={
                "reference": str(reference),
                "order_status": next_order_status,
                "provider_status": provider_status,
                "transaction_id": str(transaction.get("id")) if transaction.get("id") else None,
            },
        )

    return WompiWebhookResponse(ok=True, processed=True, reference=str(reference), status=next_order_status)


def _process_wompi_transaction_reconciliation(transaction: dict[str, Any], reference_hint: str | None = None) -> WompiWebhookResponse:
    reference = str(transaction.get("reference") or reference_hint or "").strip()
    provider_status = str(transaction.get("status") or "PENDING").upper()
    if not reference:
        return WompiWebhookResponse(ok=True, processed=False, status=_wompi_order_status(provider_status))

    existing = repository.get_payment_order_by_reference(reference)
    if not existing:
        return WompiWebhookResponse(ok=True, processed=False, reference=reference, status=_wompi_order_status(provider_status))
    _validate_wompi_transaction_against_order(transaction, existing)

    next_order_status = _wompi_order_status(provider_status)
    approved_at = parse_approved_at(transaction) if provider_status == "APPROVED" else None
    updated_order = repository.update_payment_order_status(
        reference,
        status=next_order_status,
        provider_transaction_id=str(transaction.get("id")) if transaction.get("id") else None,
        provider_status=provider_status,
        webhook_payload={"source": "reconciliation", "transaction": transaction},
        approved_at=approved_at,
    )
    if not updated_order:
        return WompiWebhookResponse(ok=True, processed=False, reference=reference, status=next_order_status)

    case_record = repository.get_case_by_id(str(existing["case_id"]))
    if case_record and (case_record.get("payment_status") != "pagado" or provider_status == "APPROVED"):
        repository.update_case_payment(
            str(existing["case_id"]),
            reference,
            payment_status=_wompi_case_payment_status(provider_status),
        )
        if provider_status == "APPROVED":
            _ensure_payment_artifacts(str(existing["case_id"]))
        repository.create_event(
            case_id=str(existing["case_id"]),
            event_type="payment_reconciled",
            actor_type="system",
            actor_id=None,
            payload={
                "reference": reference,
                "order_status": next_order_status,
                "provider_status": provider_status,
                "transaction_id": str(transaction.get("id")) if transaction.get("id") else None,
            },
        )

    return WompiWebhookResponse(ok=True, processed=True, reference=reference, status=next_order_status)


@app.post("/payments/wompi/webhook", response_model=WompiWebhookResponse)
async def wompi_webhook(request: Request) -> WompiWebhookResponse:
    if settings.wompi_environment == "sandbox":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este entorno espera eventos sandbox.")
    payload = await request.json()
    return _process_wompi_webhook(payload)


@app.post("/payments/wompi/webhook/sandbox", response_model=WompiWebhookResponse)
async def wompi_webhook_sandbox(request: Request) -> WompiWebhookResponse:
    if settings.wompi_environment != "sandbox":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este entorno no está configurado como sandbox.")
    payload = await request.json()
    return _process_wompi_webhook(payload)


@app.post("/payments/wompi/reconcile", response_model=WompiWebhookResponse)
def wompi_reconcile_payment(
    payload: WompiReconcileRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> WompiWebhookResponse:
    transaction = fetch_transaction(payload.transaction_id)
    reference = str(transaction.get("reference") or payload.reference or "").strip()
    if not reference:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Wompi no devolvio una referencia valida.")
    order = repository.get_payment_order_by_reference(reference)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No existe una orden con esa referencia.")
    if str(order["user_id"]) != str(current_user["id"]) and not _is_internal(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes acceso a este pago.")
    return _process_wompi_transaction_reconciliation(transaction, reference)


@app.get("/internal/cases", response_model=list[CaseResponse])
def list_internal_cases(
    status_filter: str | None = None,
    workflow_type: str | None = None,
    category: str | None = None,
    _: dict[str, Any] = Depends(get_internal_user),
) -> list[CaseResponse]:
    cases = repository.list_internal_cases(status=status_filter, workflow_type=workflow_type, category=category)
    return [_normalize_case(_reconcile_case_payment(case)) for case in cases]


@app.get("/internal/analytics/overview")
def internal_marketing_overview(days: int = 30, _: dict[str, Any] = Depends(get_internal_user)) -> dict[str, Any]:
    window_days = max(1, min(days, 180))
    cases = repository.list_internal_cases()
    event_counts = repository.get_marketing_event_counts(days=window_days)
    event_counts_7d = repository.get_marketing_event_counts(days=7)
    event_counts_30d = repository.get_marketing_event_counts(days=30)
    event_counts_prev_7d = repository.get_marketing_event_counts_window(from_days=14, to_days=7)
    event_counts_prev_30d = repository.get_marketing_event_counts_window(from_days=60, to_days=30)
    top_pages = repository.get_marketing_top_pages(days=window_days, limit=8)
    channels_current = repository.get_marketing_breakdown(days=7, dimension="channel", limit=8)
    channels_previous = repository.get_marketing_breakdown_window(from_days=14, to_days=7, dimension="channel", limit=8)
    campaigns_current = repository.get_marketing_breakdown(days=7, dimension="campaign", limit=8)
    campaigns_previous = repository.get_marketing_breakdown_window(from_days=14, to_days=7, dimension="campaign", limit=8)

    diagnosed = sum(1 for item in cases if str(item.get("estado") or "") in {"diagnosticado", "checkout_pendiente", "pagado_pendiente_intake", "pagado_en_revision", "en_revision", "entregado"})
    checkout_started = sum(1 for item in cases if str(item.get("estado") or "") == "checkout_pendiente")
    paid_cases = sum(1 for item in cases if str(item.get("payment_status") or "") == "pagado")
    intake_submitted = sum(1 for item in cases if str(item.get("estado") or "") in {"pagado_en_revision", "en_revision", "entregado"})
    delivered_cases = sum(1 for item in cases if str(item.get("estado") or "") == "entregado")

    funnel = {
        "diagnosed": diagnosed,
        "checkout_started": checkout_started,
        "paid_cases": paid_cases,
        "intake_submitted": intake_submitted,
        "delivered_cases": delivered_cases,
    }
    drop_alerts = [
        *_build_drop_alerts(channels_current, channels_previous, "canal"),
        *_build_drop_alerts(campaigns_current, campaigns_previous, "campana"),
    ]
    config = repository.get_marketing_config()
    return {
        "window_days": window_days,
        "event_counts": event_counts,
        "comparison": {
            "last_7d": event_counts_7d,
            "last_30d": event_counts_30d,
            "prev_7d": event_counts_prev_7d,
            "prev_30d": event_counts_prev_30d,
        },
        "funnel": funnel,
        "top_pages": top_pages,
        "channels_7d": channels_current,
        "campaigns_7d": campaigns_current,
        "drop_alerts": drop_alerts,
        "marketing_config": {
            "cta_variant": config.get("cta_variant"),
            "cta_label": config.get("cta_label"),
            "raffle_label": config.get("raffle_label"),
        },
        "marketing_agent": _build_marketing_suggestions(funnel=funnel, event_counts=event_counts, drop_alerts=drop_alerts),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/internal/marketing/config")
def update_internal_marketing_config(payload: dict[str, Any], _: dict[str, Any] = Depends(get_internal_user)) -> dict[str, Any]:
    cta_variant = str(payload.get("cta_variant") or "default").strip().lower()
    cta_label = str(payload.get("cta_label") or "").strip() or "Soluciona tu caso EPS y participa"
    raffle_label = str(payload.get("raffle_label") or "").strip() or "Rifa mayo: posibilidad de llevarse $2.500.000 COP"
    if cta_variant not in {"default", "urgencia", "confianza", "sorteo"}:
        raise HTTPException(status_code=400, detail="cta_variant no valido.")
    updated = repository.update_marketing_config(
        cta_variant=cta_variant[:40],
        cta_label=cta_label[:120],
        raffle_label=raffle_label[:140],
    )
    return {"ok": True, "config": updated}


@app.post("/internal/notifications/whatsapp/abandonment/run")
def run_whatsapp_abandonment_reminders(
    dry_run: bool = True,
    _: dict[str, Any] = Depends(get_internal_user),
) -> dict[str, Any]:
    return _run_whatsapp_abandonment_reminders(dry_run=dry_run)


@app.get("/internal/cases/{case_id}", response_model=CaseDetailResponse)
def get_internal_case(case_id: str, _: dict[str, Any] = Depends(get_internal_user)) -> CaseDetailResponse:
    case = repository.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    return _snapshot_case_detail(case)


@app.post("/internal/cases/{case_id}/status", response_model=CaseDetailResponse)
def update_internal_status(
    case_id: str,
    payload: InternalStatusUpdateRequest,
    current_user: dict[str, Any] = Depends(get_internal_user),
) -> CaseDetailResponse:
    case = repository.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    updated = repository.update_case_status(case_id, status=payload.status)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible actualizar el estado.")

    repository.create_event(
        case_id=case_id,
        event_type="internal_status_updated",
        actor_type="internal",
        actor_id=str(current_user["id"]),
        payload={"status": payload.status, "note": payload.note},
    )
    return _snapshot_case_detail(updated)


@app.post("/internal/cases/{case_id}/deliver", response_model=CaseDetailResponse)
def deliver_guest_case(
    case_id: str,
    payload: GuestDeliveryRequest,
    current_user: dict[str, Any] = Depends(get_internal_user),
) -> CaseDetailResponse:
    case = repository.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    filename = build_pdf_filename(case, payload.document_title)
    pdf_bytes = render_text_pdf(title=payload.document_title, text=payload.document_text)
    target_dir = ensure_upload_root() / "deliveries" / str(case_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = target_dir / filename
    pdf_path.write_bytes(pdf_bytes)
    relative_path = pdf_path.relative_to(ensure_upload_root()).as_posix()
    repository.create_case_file(
        case_id=case_id,
        uploaded_by=None,
        file_kind="delivery_document",
        original_name=filename,
        stored_name=filename,
        mime_type="application/pdf",
        file_size=pdf_path.stat().st_size,
        relative_path=relative_path,
        metadata={"generated_by": "internal_delivery"},
    )
    repository.update_case_document(case_id, payload.document_text)
    refreshed_case = repository.get_case_by_id(case_id) or case
    delivery_package = build_delivery_package(refreshed_case, relative_path)
    merged_summary = _merge_submission_summary(
        refreshed_case,
        customer_guide=delivery_package.get("customer_guide") or build_customer_guide(refreshed_case),
        delivery_package=delivery_package,
    )
    email_result = send_guest_delivery_email(
        recipient=refreshed_case.get("usuario_email"),
        case=refreshed_case,
        delivery_package=delivery_package,
        note=payload.delivery_note,
        attachments=[{"relative_path": relative_path, "filename": filename, "mime_type": "application/pdf"}],
    )
    email_status = str(email_result.get("status") or "").lower()
    if email_status != "sent":
        repository.create_event(
            case_id=case_id,
            event_type="guest_delivery_email_failed",
            actor_type="internal",
            actor_id=str(current_user["id"]),
            payload={"filename": filename, "email_result": email_result},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo enviar el correo al cliente. Estado: {email_result.get('status') or 'desconocido'}.",
        )
    whatsapp_result = (
        send_guest_delivery_whatsapp(phone=refreshed_case.get("usuario_telefono"), case=refreshed_case, delivery_package=delivery_package)
        if payload.send_whatsapp
        else {"status": "skipped", "reason": "disabled"}
    )
    updated = repository.update_case_status(
        case_id,
        status="entregado",
        submission_summary={
            **merged_summary,
            "delivery_package": delivery_package,
            "delivery_email": email_result,
            "delivery_whatsapp": whatsapp_result,
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "delivered_by": str(current_user["id"]),
        },
    ) or refreshed_case
    repository.create_event(
        case_id=case_id,
        event_type="guest_case_delivered",
        actor_type="internal",
        actor_id=str(current_user["id"]),
        payload={"filename": filename, "email_status": email_result.get("status"), "whatsapp_status": whatsapp_result.get("status")},
    )
    updated = _persist_guest_ops(updated)
    return _snapshot_case_detail(updated)


@app.post("/internal/cases/{case_id}/deliver-upload", response_model=CaseDetailResponse)
async def deliver_guest_case_upload(
    case_id: str,
    file: UploadFile = File(...),
    delivery_note: str = Form(default=""),
    send_whatsapp: bool = Form(default=True),
    current_user: dict[str, Any] = Depends(get_internal_user),
) -> CaseDetailResponse:
    case = repository.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    allowed_mime = {
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    }
    if str(file.content_type or "").lower() not in allowed_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no permitido. Sube PDF o DOCX.",
        )

    saved = save_upload(file, bucket="deliveries", owner_id=str(case_id))
    repository.create_case_file(
        case_id=case_id,
        uploaded_by=str(current_user["id"]),
        file_kind="delivery_document",
        original_name=saved["original_name"],
        stored_name=saved["stored_name"],
        mime_type=saved["mime_type"],
        file_size=saved["file_size"],
        relative_path=saved["relative_path"],
        metadata={"generated_by": "internal_upload_delivery"},
    )

    refreshed_case = repository.get_case_by_id(case_id) or case
    delivery_package = build_delivery_package(refreshed_case, saved["relative_path"])
    merged_summary = _merge_submission_summary(
        refreshed_case,
        customer_guide=delivery_package.get("customer_guide") or build_customer_guide(refreshed_case),
        delivery_package=delivery_package,
    )
    email_result = send_guest_delivery_email(
        recipient=refreshed_case.get("usuario_email"),
        case=refreshed_case,
        delivery_package=delivery_package,
        note=delivery_note or None,
        attachments=[{"relative_path": saved["relative_path"], "filename": saved["original_name"], "mime_type": saved["mime_type"]}],
    )
    email_status = str(email_result.get("status") or "").lower()
    if email_status != "sent":
        repository.create_event(
            case_id=case_id,
            event_type="guest_delivery_email_failed",
            actor_type="internal",
            actor_id=str(current_user["id"]),
            payload={"filename": saved["original_name"], "email_result": email_result},
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"No se pudo enviar el correo al cliente. Estado: {email_result.get('status') or 'desconocido'}.",
        )
    whatsapp_result = (
        send_guest_delivery_whatsapp(phone=refreshed_case.get("usuario_telefono"), case=refreshed_case, delivery_package=delivery_package)
        if send_whatsapp
        else {"status": "skipped", "reason": "disabled"}
    )
    updated = repository.update_case_status(
        case_id,
        status="entregado",
        submission_summary={
            **merged_summary,
            "delivery_package": delivery_package,
            "delivery_email": email_result,
            "delivery_whatsapp": whatsapp_result,
            "delivery_uploaded_file": {
                "relative_path": saved["relative_path"],
                "original_name": saved["original_name"],
                "mime_type": saved["mime_type"],
            },
            "delivered_at": datetime.now(timezone.utc).isoformat(),
            "delivered_by": str(current_user["id"]),
        },
    ) or refreshed_case
    repository.create_event(
        case_id=case_id,
        event_type="guest_case_delivered_upload",
        actor_type="internal",
        actor_id=str(current_user["id"]),
        payload={
            "filename": saved["original_name"],
            "email_status": email_result.get("status"),
            "whatsapp_status": whatsapp_result.get("status"),
        },
    )
    updated = _persist_guest_ops(updated)
    return _snapshot_case_detail(updated)
