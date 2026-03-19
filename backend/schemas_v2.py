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


class UserProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    document_number: str = Field(min_length=4, max_length=40)
    phone: str = Field(min_length=7, max_length=40)
    city: str = Field(min_length=2, max_length=80)
    department: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=5, max_length=180)


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    document_number: str | None = None
    phone: str | None = None
    city: str | None = None
    department: str | None = None
    address: str | None = None
    role: str
    created_at: datetime
    updated_at: datetime


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class AnalysisPreviewRequest(BaseModel):
    category: str = Field(min_length=2, max_length=80)
    department: str = Field(min_length=2, max_length=80)
    city: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=20, max_length=6000)
    prior_actions: list[str] = Field(default_factory=list)
    form_data: dict[str, Any] = Field(default_factory=dict)
    attachment_ids: list[str] = Field(default_factory=list)


class RoutingTargetResponse(BaseModel):
    type: str
    name: str
    channel: str | None = None
    contact: str | None = None
    automatable: bool = False
    genera_radicado: bool = False
    subject_suggested: str | None = None
    reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisPreviewResponse(BaseModel):
    facts: dict[str, Any]
    legal_analysis: dict[str, Any]
    strategy: str
    recommended_action: str
    workflow_type: str
    prerequisites: list[dict[str, Any]]
    warnings: list[str]
    routing: dict[str, Any]
    dx_result: dict[str, Any] = Field(default_factory=dict)
    pending_questions: list[dict[str, Any]] = Field(default_factory=list)
    case_route: str | None = None
    tutela_procedencia: dict[str, Any] = Field(default_factory=dict)
    source_validation_policy: dict[str, Any] = Field(default_factory=dict)
    layer_outputs: dict[str, Any] = Field(default_factory=dict)


class UploadedFileResponse(BaseModel):
    id: str
    case_id: str | None = None
    file_kind: str
    status: str
    original_name: str
    mime_type: str
    file_size: int
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class CaseCreateRequest(AnalysisPreviewRequest):
    attachment_ids: list[str] = Field(default_factory=list)


class CaseIntakeUpdateRequest(BaseModel):
    description: str = Field(min_length=20, max_length=8000)
    form_data: dict[str, Any] = Field(default_factory=dict)


class PaymentConfirmationRequest(BaseModel):
    reference: str = Field(min_length=3, max_length=80)


class CatalogProductResponse(BaseModel):
    code: str
    name: str
    price_cop: int
    price_with_filing_cop: int
    currency: str
    short_description: str
    detailed_description: str
    next_step_hint: str
    supports_filing: bool = True


class EntityRoutingChannelResponse(BaseModel):
    channel: str | None = None
    contact: str | None = None
    automatable: bool = False
    genera_radicado: bool = False
    response_window: str | None = None
    notes: str | None = None


class EntityAutocompleteResponse(BaseModel):
    name: str
    type: str | None = None
    sector: str | None = None
    nit: str | None = None
    address: str | None = None
    city: str | None = None
    department: str | None = None
    phone: str | None = None
    phones: list[str] = Field(default_factory=list)
    pqrs_emails: list[str] = Field(default_factory=list)
    notification_emails: list[str] = Field(default_factory=list)
    website: str | None = None
    legal_representative: str | None = None
    superintendence: str | None = None
    source: str | None = None
    verified: bool = False
    routing_channels: list[EntityRoutingChannelResponse] = Field(default_factory=list)


class WompiCheckoutSessionRequest(BaseModel):
    product_code: str | None = Field(default=None, min_length=3, max_length=80)
    include_filing: bool = False


class PaymentOrderResponse(BaseModel):
    id: str
    case_id: str
    user_id: str
    provider: str
    environment: str
    product_code: str
    product_name: str
    include_filing: bool
    amount_cop: int
    amount_in_cents: int
    currency: str
    reference: str
    status: str
    provider_transaction_id: str | None = None
    provider_status: str | None = None
    checkout_payload: dict[str, Any] = Field(default_factory=dict)
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class WompiCheckoutSessionResponse(BaseModel):
    order: PaymentOrderResponse
    checkout: dict[str, Any] = Field(default_factory=dict)


class WompiWebhookResponse(BaseModel):
    ok: bool
    processed: bool
    reference: str | None = None
    status: str | None = None


class WompiReconcileRequest(BaseModel):
    transaction_id: str = Field(min_length=3, max_length=120)
    reference: str | None = Field(default=None, min_length=3, max_length=120)


class CaseSubmitRequest(BaseModel):
    mode: str = Field(pattern="^(auto|manual_contact|presencial)$")
    manual_contact: str | None = Field(default=None, max_length=180)
    notes: str | None = Field(default=None, max_length=500)
    signature: dict[str, Any] = Field(default_factory=dict)
    reviewed_document: bool = False
    judicial_destination_confirmed: bool = False


class ManualRadicadoRequest(BaseModel):
    radicado: str = Field(min_length=3, max_length=120)
    notes: str | None = Field(default=None, max_length=500)
    signature: dict[str, Any] = Field(default_factory=dict)
    reviewed_document: bool = False


class InternalStatusUpdateRequest(BaseModel):
    status: str = Field(min_length=3, max_length=80)
    note: str | None = Field(default=None, max_length=500)


class SubmissionAttemptResponse(BaseModel):
    id: str
    channel: str
    destination_name: str | None = None
    destination_contact: str | None = None
    subject: str | None = None
    cc: list[str] = Field(default_factory=list)
    status: str
    radicado: str | None = None
    response_payload: dict[str, Any] = Field(default_factory=dict)
    error_text: str | None = None
    created_at: datetime
    updated_at: datetime


class TimelineEventResponse(BaseModel):
    id: str
    event_type: str
    actor_type: str
    actor_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class CaseResponse(BaseModel):
    id: str
    user_id: str | None = None
    user_name: str
    user_email: EmailStr
    user_document: str | None = None
    user_phone: str | None = None
    user_city: str | None = None
    user_department: str | None = None
    user_address: str | None = None
    category: str
    workflow_type: str
    description: str
    recommended_action: str | None = None
    strategy_text: str | None = None
    facts: dict[str, Any] = Field(default_factory=dict)
    legal_analysis: dict[str, Any] = Field(default_factory=dict)
    routing: dict[str, Any] = Field(default_factory=dict)
    dx_result: dict[str, Any] = Field(default_factory=dict)
    pending_questions: list[dict[str, Any]] = Field(default_factory=list)
    case_route: str | None = None
    tutela_procedencia: dict[str, Any] = Field(default_factory=dict)
    source_validation_policy: dict[str, Any] = Field(default_factory=dict)
    layer_outputs: dict[str, Any] = Field(default_factory=dict)
    final_validation: dict[str, Any] = Field(default_factory=dict)
    prerequisites: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status: str
    payment_status: str
    payment_reference: str | None = None
    generated_document: str | None = None
    submission_summary: dict[str, Any] = Field(default_factory=dict)
    attachments: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CaseDetailResponse(BaseModel):
    case: CaseResponse
    files: list[UploadedFileResponse] = Field(default_factory=list)
    submission_attempts: list[SubmissionAttemptResponse] = Field(default_factory=list)
    timeline: list[TimelineEventResponse] = Field(default_factory=list)


class DocumentGenerateRequest(BaseModel):
    regeneration_reason: str | None = Field(default=None, max_length=2000)
    additional_context: str | None = Field(default=None, max_length=4000)


class CaseDocumentResponse(BaseModel):
    case: CaseResponse
    document: str
    quality_review: dict[str, Any] | None = None
