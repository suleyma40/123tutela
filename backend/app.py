from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from backend import repository
from backend.analysis import build_document, build_routing, summarize_action
from backend.config import settings
from backend.schemas import (
    AnalysisPreviewRequest,
    AnalysisPreviewResponse,
    AuthResponse,
    CaseCreateRequest,
    CaseDocumentResponse,
    CaseResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from backend.security import create_token, decode_token, hash_password, verify_password
from backend.legal_service import LegalAnalyzer

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = LegalAnalyzer(settings.knowledge_base_json)


def _normalize_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(case["id"]),
        "user_id": str(case["user_id"]),
        "user_name": case["usuario_nombre"],
        "user_email": case["usuario_email"],
        "user_city": case.get("usuario_ciudad"),
        "user_department": case.get("usuario_departamento"),
        "category": case["categoria"],
        "description": case["descripcion"],
        "recommended_action": case["recommended_action"],
        "strategy_text": case["strategy_text"],
        "routing": case.get("routing") or {},
        "status": case["estado"],
        "generated_document": case.get("generated_document"),
        "created_at": case["created_at"],
        "updated_at": case["updated_at"],
    }


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


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> AuthResponse:
    existing = repository.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese correo ya está registrado.")

    user = repository.create_user(payload.name, payload.email, hash_password(payload.password))
    token = create_token(str(user["id"]), user["email"], settings.jwt_secret)
    return AuthResponse(token=token, user=UserResponse(**user))


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest) -> AuthResponse:
    user = repository.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas.")

    token = create_token(str(user["id"]), user["email"], settings.jwt_secret)
    safe_user = {key: value for key, value in user.items() if key != "password_hash"}
    return AuthResponse(token=token, user=UserResponse(**safe_user))


@app.get("/auth/me", response_model=UserResponse)
def me(current_user: dict[str, Any] = Depends(get_current_user)) -> UserResponse:
    return UserResponse(**current_user)


@app.post("/analysis/preview", response_model=AnalysisPreviewResponse)
def analysis_preview(payload: AnalysisPreviewRequest) -> AnalysisPreviewResponse:
    result = analyzer.full_analysis(payload.description, category=payload.category)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    strategy = result["strategy"]
    legal_analysis = result["legal_analysis"]
    recommended_action = summarize_action(strategy, legal_analysis)
    routing = build_routing(payload.category, payload.city, payload.department, result["facts"])
    return AnalysisPreviewResponse(
        facts=result["facts"],
        legal_analysis=legal_analysis,
        strategy=strategy,
        recommended_action=recommended_action,
        routing=routing,
    )


@app.post("/cases", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreateRequest, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseResponse:
    result = analyzer.full_analysis(payload.description, category=payload.category)
    if not result.get("success"):
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result.get("error"))

    strategy = result["strategy"]
    legal_analysis = result["legal_analysis"]
    facts = result["facts"]
    recommended_action = summarize_action(strategy, legal_analysis)
    routing = build_routing(payload.category, payload.city, payload.department, facts)

    case = repository.create_case_record(
        user_id=str(current_user["id"]),
        user_name=current_user["name"],
        user_email=current_user["email"],
        city=payload.city,
        department=payload.department,
        category=payload.category,
        description=payload.description,
        attachments=payload.attachments,
        recommended_action=recommended_action,
        strategy_text=strategy,
        facts=facts,
        legal_analysis=legal_analysis,
        routing=routing,
    )
    return CaseResponse(**_normalize_case(case))


@app.get("/cases", response_model=list[CaseResponse])
def list_cases(current_user: dict[str, Any] = Depends(get_current_user)) -> list[CaseResponse]:
    cases = repository.list_cases_for_user(str(current_user["id"]))
    return [CaseResponse(**_normalize_case(case)) for case in cases]


@app.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")
    return CaseResponse(**_normalize_case(case))


@app.post("/cases/{case_id}/document", response_model=CaseDocumentResponse)
def generate_document(case_id: str, current_user: dict[str, Any] = Depends(get_current_user)) -> CaseDocumentResponse:
    case = repository.get_case_for_user(case_id, str(current_user["id"]))
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trámite no encontrado.")

    document = build_document(case)
    updated = repository.update_case_document(case_id, document)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fue posible generar el documento.")

    normalized = _normalize_case(updated)
    return CaseDocumentResponse(case=CaseResponse(**normalized), document=document)
