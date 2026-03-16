from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.catalog_runtime import get_product, list_catalog, suggest_product_code
from backend.config import settings
from backend.document_quality import evaluate_generated_document
from backend.entity_directory import search_entity_directory
from backend.document_rules import evaluate_document_rule
from backend.intake_validation import validate_intake, validate_submission_readiness
from backend.legal_service import LegalAnalyzer
from backend.notifications import send_post_radicado_email
from backend.schemas_v2 import (
    AnalysisPreviewRequest,
    AnalysisPreviewResponse,
    AuthResponse,
    CatalogProductResponse,
    EntityAutocompleteResponse,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseDocumentResponse,
    CaseIntakeUpdateRequest,
    CaseResponse,
    CaseSubmitRequest,
    InternalStatusUpdateRequest,
    LoginRequest,
    ManualRadicadoRequest,
    PaymentOrderResponse,
    PaymentConfirmationRequest,
    RegisterRequest,
    UploadedFileResponse,
    UserProfileUpdateRequest,
    UserResponse,
    WompiCheckoutSessionRequest,
    WompiCheckoutSessionResponse,
    WompiReconcileRequest,
    WompiWebhookResponse,
)
from backend.security import create_token, decode_token, hash_password, verify_password
from backend.storage import absolute_path, move_relative_path, save_upload
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
    build_document,
    build_submission_guidance,
    build_routing,
    build_strategy_text,
    generate_radicado,
    infer_workflow,
    user_profile_complete,
)


app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = LegalAnalyzer(settings.knowledge_base_json)


def _normalize_user(user: dict[str, Any]) -> UserResponse:
    safe_user = {key: value for key, value in user.items() if key != "password_hash"}
    if safe_user.get("id") is not None:
        safe_user["id"] = str(safe_user["id"])
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
        facts=case.get("facts") or {},
        legal_analysis=case.get("legal_analysis") or {},
        routing=case.get("routing") or {},
        prerequisites=case.get("prerequisites") or [],
        warnings=case.get("warnings") or [],
        status=case.get("estado") or "borrador",
        payment_status=case.get("payment_status") or "pendiente",
        payment_reference=case.get("payment_reference"),
        generated_document=case.get("generated_document"),
        submission_summary=case.get("submission_summary") or {},
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
) -> dict[str, Any]:
    updater = repository.update_case_submission if manual_contact is not None else repository.update_case_status
    update_kwargs: dict[str, Any] = {
        "status": current_status,
        "submission_summary": {
            **(base_case.get("submission_summary") or {}),
            "guidance": guidance,
            "post_radicado_email": email_result,
        },
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
        user_id=str(order["user_id"]),
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


def _merge_intake_into_facts(
    *,
    existing_facts: dict[str, Any],
    form_data: dict[str, Any],
    description: str,
    category: str | None,
) -> dict[str, Any]:
    facts = dict(existing_facts or {})
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

    if category and not facts.get("problema_central"):
        facts["problema_central"] = category

    facts["intake_form"] = form_data or {}
    return facts


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
    attempts = repository.list_submission_attempts(str(case["id"]))
    events = repository.list_case_events(str(case["id"]))
    return CaseDetailResponse(
        case=_normalize_case(case),
        files=[_normalize_file(item) for item in files],
        submission_attempts=_normalize_attempts(attempts),
        timeline=_normalize_timeline(events),
    )


def _is_internal(user: dict[str, Any]) -> bool:
    return user.get("role") == "internal"


def _require_profile(user: dict[str, Any]) -> None:
    if not user_profile_complete(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completa tu perfil antes de crear, radicar o generar documentos.",
        )


def get_current_user(authorization: str = Header(default="")) -> dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión requerida.")

    token = authorization.replace("Bearer ", "", 1).strip()
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
    return "internal" if email.lower() in settings.internal_admin_emails else "citizen"


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.get("/catalog/products", response_model=list[CatalogProductResponse])
def get_catalog_products() -> list[CatalogProductResponse]:
    return [CatalogProductResponse(**product) for product in list_catalog()]


@app.get("/catalog/entities", response_model=list[EntityAutocompleteResponse])
def get_catalog_entities(q: str, limit: int = 8) -> list[EntityAutocompleteResponse]:
    if len(q.strip()) < 2:
        return []
    entities = search_entity_directory(q, limit=max(1, min(limit, 12)))
    return [EntityAutocompleteResponse(**entity) for entity in entities]


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> AuthResponse:
    existing = repository.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese correo ya está registrado.")

    role = _role_for_email(payload.email)
    user = repository.create_user(payload.name, payload.email, hash_password(payload.password), role=role)
    token = create_token(str(user["id"]), user["email"], settings.jwt_secret)
    return AuthResponse(token=token, user=_normalize_user(user))


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = repository.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas.")

    token = create_token(str(user["id"]), user["email"], settings.jwt_secret)
    return AuthResponse(token=token, user=_normalize_user(user))


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    return _normalize_user(current_user)


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
def analysis_preview(payload: AnalysisPreviewRequest) -> AnalysisPreviewResponse:
    result = analyzer.full_analysis(payload.description, category=payload.category)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    workflow = infer_workflow(
        category=payload.category,
        description=payload.description,
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
        description=payload.description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=payload.category,
        description=payload.description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
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
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
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
    )


@app.post("/cases", response_model=CaseDetailResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreateRequest, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDetailResponse:
    _require_profile(current_user)

    result = analyzer.full_analysis(payload.description, category=payload.category)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    workflow = infer_workflow(
        category=payload.category,
        description=payload.description,
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
        description=payload.description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=payload.category,
        description=payload.description,
        facts=result["facts"],
        prior_actions=payload.prior_actions,
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
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
    )
    blocking_issues = list(
        dict.fromkeys(
            intake_review.get("blocking_issues", [])
            + preview_gate.get("blocking_issues", [])
            + document_rule_review.get("blocking_issues", [])
        )
    )
    if blocking_issues:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No es posible crear el expediente todavia. Corrige esto primero: " + " | ".join(blocking_issues),
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
        description=payload.description,
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
        payload={"workflow_type": workflow["workflow_type"], "recommended_action": workflow["recommended_action"]},
    )
    return _snapshot_case_detail(case)


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
    facts = _merge_intake_into_facts(
        existing_facts=case.get("facts") or {},
        form_data=payload.form_data or {},
        description=payload.description,
        category=category,
    )
    legal_analysis = case.get("legal_analysis") or {}
    workflow = infer_workflow(
        category=category,
        description=payload.description,
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
        description=payload.description,
        facts=facts,
        prior_actions=prior_actions,
    )
    preview_gate = validate_submission_readiness(
        category=category,
        description=payload.description,
        facts=facts,
        prior_actions=prior_actions,
    )
    document_rule_review = evaluate_document_rule(
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        description=payload.description,
        facts=facts,
    )
    facts["intake_review"] = intake_review
    facts["preview_gate"] = preview_gate
    facts["document_rule_review"] = document_rule_review
    combined_warnings = (
        workflow["warnings"]
        + intake_review.get("blocking_issues", [])
        + intake_review.get("warnings", [])
        + preview_gate.get("blocking_issues", [])
        + preview_gate.get("warnings", [])
        + document_rule_review.get("blocking_issues", [])
        + document_rule_review.get("warnings", [])
    )
    updated = repository.update_case_intake(
        case_id,
        workflow_type=workflow["workflow_type"],
        description=payload.description,
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
        payload={"description_length": len(payload.description), "fields": sorted((payload.form_data or {}).keys())},
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

    repository.create_event(
        case_id=case_id,
        event_type="payment_confirmed",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={"reference": payload.reference},
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
    if case.get("payment_status") == "pagado":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Este trámite ya tiene un pago aprobado.")

    product_code = payload.product_code or suggest_product_code(case.get("recommended_action"))
    product = get_product(product_code or "")
    if not product:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fue posible determinar el producto a cobrar.")

    amount_cop = product.price_with_filing_cop if payload.include_filing else product.price_cop
    amount_in_cents = amount_cop_to_cents(amount_cop)
    reference = build_reference(case_id, product.code)
    product_name = product.name if not payload.include_filing else f"{product.name} + radicación"
    checkout = build_checkout_payload(
        reference=reference,
        amount_in_cents=amount_in_cents,
        product_name=product_name,
        description=product.short_description,
        customer_email=current_user["email"],
    )
    order = repository.create_payment_order(
        case_id=case_id,
        user_id=str(current_user["id"]),
        environment=settings.wompi_environment,
        product_code=product.code,
        product_name=product_name,
        include_filing=payload.include_filing,
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
            "product_code": product.code,
            "product_name": product_name,
            "include_filing": payload.include_filing,
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
def generate_document(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDocumentResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    if case.get("payment_status") != "pagado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes registrar el pago antes de generar el documento.")

    document_rule_review = evaluate_document_rule(
        recommended_action=case.get("recommended_action"),
        workflow_type=case.get("workflow_type"),
        description=case.get("descripcion") or "",
        facts=case.get("facts") or {},
    )
    if document_rule_review.get("blocking_issues"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Todavia faltan datos minimos para generar este documento: "
            + " | ".join(document_rule_review["blocking_issues"]),
        )

    document = build_document(case)
    quality_review = evaluate_generated_document(case, document)
    if not quality_review.get("passed"):
        repository.create_event(
            case_id=case_id,
            event_type="document_generation_blocked",
            actor_type="system",
            actor_id=None,
            payload={
                "score": quality_review.get("score"),
                "threshold": quality_review.get("threshold"),
                "blocking_issues": quality_review.get("blocking_issues"),
                "warnings": quality_review.get("warnings"),
            },
        )
        detail_parts = quality_review.get("blocking_issues") or quality_review.get("warnings") or [
            "El borrador no alcanzo la calidad juridica minima.",
        ]
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"El borrador no alcanza el umbral minimo de calidad ({quality_review.get('score')}/"
                f"{quality_review.get('threshold')}). " + " | ".join(detail_parts)
            ),
        )
    updated = repository.update_case_document(case_id, document)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible generar el documento.")
    updated = repository.update_case_status(
        case_id,
        status=updated.get("estado") or "listo_para_envio",
        submission_summary={
            **(updated.get("submission_summary") or {}),
            "document_quality": quality_review,
        },
    ) or updated

    repository.create_event(
        case_id=case_id,
        event_type="document_generated",
        actor_type="system",
        actor_id=None,
        payload={"length": len(document), "score": quality_review.get("score"), "threshold": quality_review.get("threshold")},
    )
    return CaseDocumentResponse(case=_normalize_case(updated), document=document, quality_review=quality_review)


@app.post("/cases/{case_id}/submit", response_model=CaseDetailResponse)
def submit_case(
    case_id: str,
    payload: CaseSubmitRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    if case.get("payment_status") != "pagado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes registrar el pago antes de radicar.")
    if not case.get("generated_document"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Genera el documento antes de radicar.")

    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}
    channel = primary.get("channel") or routing.get("channel") or "manual"
    destination_name = primary.get("name")
    destination_contact = primary.get("contact")
    subject = routing.get("subject")
    cc_list = [case.get("usuario_email")] if case.get("usuario_email") else []

    status_value = "enviado"
    manual_contact = {}
    response_payload = {
        "mode": payload.mode,
        "notes": payload.notes,
    }
    radicado = None

    if payload.mode == "auto":
        if not routing.get("automatable") or not destination_contact:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este caso no tiene canal automático confiable.")
        if routing.get("genera_radicado"):
            status_value = "radicado"
            radicado = generate_radicado("RAD")
        attempt_status = "success"
    elif payload.mode == "manual_contact":
        if not payload.manual_contact:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes ingresar un contacto manual.")
        destination_contact = payload.manual_contact
        manual_contact = {"value": payload.manual_contact, "notes": payload.notes}
        channel = "email" if "@" in payload.manual_contact else "manual"
        status_value = "enviado" if "@" in payload.manual_contact else "requiere_accion_manual"
        attempt_status = "manual_contact"
    else:
        manual_contact = {"mode": "presencial", "notes": payload.notes}
        status_value = "requiere_accion_manual"
        attempt_status = "presencial_required"
        response_payload["instructions"] = routing.get("fallback", {}).get("instructions") or []

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
    updated = _apply_post_radicado_email_result(
        case_id=case_id,
        base_case=updated,
        current_status=updated.get("estado") or status_value,
        manual_contact=updated.get("manual_contact") or manual_contact,
        guidance=guidance,
        email_result=email_result,
    )

    repository.create_event(
        case_id=case_id,
        event_type="submission_attempted",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={"mode": payload.mode, "channel": channel, "radicado": radicado},
    )
    return _snapshot_case_detail(updated)


@app.post("/cases/{case_id}/manual-radicado", response_model=CaseDetailResponse)
def register_manual_radicado(
    case_id: str,
    payload: ManualRadicadoRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    repository.create_submission_attempt(
        case_id=case_id,
        channel="manual_record",
        destination_name=(case.get("routing") or {}).get("primary_target", {}).get("name"),
        destination_contact=(case.get("routing") or {}).get("primary_target", {}).get("contact"),
        subject=(case.get("routing") or {}).get("subject"),
        cc=[case.get("usuario_email")] if case.get("usuario_email") else [],
        status="manual_radicado",
        radicado=payload.radicado,
        response_payload={"notes": payload.notes},
    )
    updated = repository.update_case_status(
        case_id,
        status="radicado",
        submission_summary={
            **(case.get("submission_summary") or {}),
            "radicado": payload.radicado,
            "manual_notes": payload.notes,
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
    updated = _apply_post_radicado_email_result(
        case_id=case_id,
        base_case=updated,
        current_status=updated.get("estado") or "radicado",
        guidance=guidance,
        email_result=email_result,
    )

    repository.create_event(
        case_id=case_id,
        event_type="manual_radicado_recorded",
        actor_type="user",
        actor_id=str(current_user["id"]),
        payload={"radicado": payload.radicado, "notes": payload.notes},
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
