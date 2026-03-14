from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class AnalysisPreviewRequest(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    department: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=20, max_length=6000)
    attachments: list[str] = Field(default_factory=list)


class RoutingTarget(BaseModel):
    type: str
    name: str
    channel: str | None = None
    contact: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisPreviewResponse(BaseModel):
    facts: dict[str, Any]
    legal_analysis: dict[str, Any]
    strategy: str
    recommended_action: str
    routing: dict[str, Any]


class CaseCreateRequest(AnalysisPreviewRequest):
    pass


class CaseResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: EmailStr
    user_city: str | None = None
    user_department: str | None = None
    category: str
    description: str
    recommended_action: str
    strategy_text: str
    routing: dict[str, Any]
    status: str
    generated_document: str | None = None
    created_at: datetime
    updated_at: datetime


class CaseDocumentResponse(BaseModel):
    case: CaseResponse
    document: str
