from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentDocument:
    code: str
    name: str
    workflow_type: str
    recommended_action: str
    stage: str
    description: str
    product_code: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


HEALTH_BLOCK_DOCUMENTS: tuple[AgentDocument, ...] = (
    AgentDocument(
        code="salud_derecho_peticion",
        name="Derecho de peticion en salud",
        workflow_type="derecho_peticion",
        recommended_action="Derecho de peticion a EPS",
        stage="previo",
        description="Peticion formal para exigir autorizacion, informacion, respuesta o entrega de servicios de salud.",
        product_code="derecho_peticion",
    ),
    AgentDocument(
        code="salud_accion_tutela",
        name="Accion de tutela en salud",
        workflow_type="tutela",
        recommended_action="Accion de tutela",
        stage="principal",
        description="Tutela para proteger salud, vida digna y derechos conexos cuando la EPS o IPS bloquea el servicio.",
        product_code="accion_tutela",
    ),
    AgentDocument(
        code="salud_impugnacion_tutela",
        name="Impugnacion de tutela en salud",
        workflow_type="impugnacion",
        recommended_action="Impugnacion de tutela",
        stage="posterior",
        description="Impugnacion de un fallo de tutela adverso o insuficiente en un caso de salud.",
        product_code="impugnacion_tutela",
    ),
    AgentDocument(
        code="salud_incidente_desacato",
        name="Incidente de desacato en salud",
        workflow_type="desacato",
        recommended_action="Incidente de desacato",
        stage="posterior",
        description="Incidente para exigir cumplimiento de un fallo de tutela ya concedido en salud.",
        product_code="incidente_desacato",
    ),
)


def list_health_block_documents() -> list[dict[str, Any]]:
    return [item.to_dict() for item in HEALTH_BLOCK_DOCUMENTS]


def resolve_health_document(
    *,
    workflow_type: str | None,
    recommended_action: str | None,
) -> AgentDocument:
    normalized_action = str(recommended_action or "").strip().lower()
    normalized_workflow = str(workflow_type or "").strip().lower()

    if "desacato" in normalized_action or normalized_workflow == "desacato":
        return HEALTH_BLOCK_DOCUMENTS[3]
    if "impugn" in normalized_action or normalized_workflow == "impugnacion":
        return HEALTH_BLOCK_DOCUMENTS[2]
    if "tutela" in normalized_action or normalized_workflow == "tutela":
        return HEALTH_BLOCK_DOCUMENTS[1]
    return HEALTH_BLOCK_DOCUMENTS[0]
