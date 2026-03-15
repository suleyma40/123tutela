from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.config import settings
from backend.legal_service import LegalAnalyzer
from backend.schemas_v2 import (
    AnalysisPreviewRequest,
    AnalysisPreviewResponse,
    AuthResponse,
    CaseCreateRequest,
    CaseDetailResponse,
    CaseDocumentResponse,
    CaseResponse,
    CaseSubmitRequest,
    InternalStatusUpdateRequest,
    LoginRequest,
    ManualRadicadoRequest,
    PaymentConfirmationRequest,
    RegisterRequest,
    UploadedFileResponse,
    UserProfileUpdateRequest,
    UserResponse,
)
from backend.security import create_token, decode_token, hash_password, verify_password
from backend.storage import absolute_path, move_relative_path, save_upload
from backend import repository_ext as repository
from backend.workflows import (
    build_document,
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


def _snapshot_case_detail(case: dict[str, Any]) -> CaseDetailResponse:
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
    return AnalysisPreviewResponse(
        facts=result["facts"],
        legal_analysis=result["legal_analysis"],
        strategy=strategy,
        recommended_action=workflow["recommended_action"],
        workflow_type=workflow["workflow_type"],
        prerequisites=workflow["prerequisites"],
        warnings=workflow["warnings"],
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
        warnings=workflow["warnings"],
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
    return [_normalize_case(case) for case in cases]


@app.get("/cases/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDetailResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    return _snapshot_case_detail(case)


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


@app.post("/cases/{case_id}/document", response_model=CaseDocumentResponse)
def generate_document(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDocumentResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    if case.get("payment_status") != "pagado":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Debes registrar el pago antes de generar el documento.")

    document = build_document(case)
    updated = repository.update_case_document(case_id, document)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible generar el documento.")

    repository.create_event(
        case_id=case_id,
        event_type="document_generated",
        actor_type="system",
        actor_id=None,
        payload={"length": len(document)},
    )
    return CaseDocumentResponse(case=_normalize_case(updated), document=document)


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
        },
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible actualizar el trámite.")

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
        },
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible registrar el radicado.")

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


@app.get("/internal/cases", response_model=list[CaseResponse])
def list_internal_cases(
    status_filter: str | None = None,
    workflow_type: str | None = None,
    category: str | None = None,
    _: dict[str, Any] = Depends(get_internal_user),
) -> list[CaseResponse]:
    cases = repository.list_internal_cases(status=status_filter, workflow_type=workflow_type, category=category)
    return [_normalize_case(case) for case in cases]


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
