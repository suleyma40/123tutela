from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import HTTPException

from backend import app_v2
from backend.storage import ensure_upload_root
from backend import workflows
from backend.schemas_v2 import CaseCreateRequest, CaseIntakeUpdateRequest


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class HealthFlowCase:
    name: str
    description: str
    category: str
    city: str
    department: str
    prior_actions: list[str]
    create_form: dict[str, Any]
    intake_update_form: dict[str, Any]
    expected_workflow: str
    expected_action: str
    expected_generate_error: str | None = None
    attachment_names: list[str] | None = None


class InMemoryRepository:
    def __init__(self) -> None:
        self.cases: dict[str, dict[str, Any]] = {}
        self.events: dict[str, list[dict[str, Any]]] = {}
        self.files_by_case: dict[str, list[dict[str, Any]]] = {}
        self.submission_attempts: dict[str, list[dict[str, Any]]] = {}
        self.payment_orders: dict[str, list[dict[str, Any]]] = {}
        self.case_counter = 0
        self.event_counter = 0
        self.submission_counter = 0

    def get_file_by_id(self, file_id: str) -> dict[str, Any] | None:
        return None

    def list_business_rules(self) -> list[dict[str, Any]]:
        return []

    def search_court_targets(self, city: str, department: str) -> list[dict[str, Any]]:
        return [
            {
                "tipo_oficina": "Juzgado Constitucional de Reparto",
                "municipio": city,
                "departamento": department,
                "correo_reparto": "reparto.tutelas@example.com",
                "correo_alternativo": "soporte.tutelas@example.com",
                "url_referencia": "",
                "codigo_interno": "NAC-001",
                "plataforma_oficial": "Correo institucional",
                "asunto_recomendado": f"Accion de tutela - {city}",
                "notas": "Smoke target",
            }
        ]

    def search_entities(self, category: str, entity_names: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "nombre_entidad": name,
                "canal_envio": "correo",
                "contacto_envio": f"pqrs.{name.lower().replace(' ', '').replace('.', '')}@example.com",
                "genera_radicado": True,
                "modulo": category,
                "paso_flujo": "pqrs",
                "plazo_respuesta": "15 dias habiles",
                "observaciones": "Smoke target",
            }
            for name in entity_names
        ]

    def create_case_record(self, **kwargs: Any) -> dict[str, Any]:
        self.case_counter += 1
        case_id = str(self.case_counter)
        created_at = _now()
        case = {
            "id": case_id,
            "user_id": kwargs["user_id"],
            "usuario_nombre": kwargs["user_name"],
            "usuario_email": kwargs["user_email"],
            "usuario_documento": kwargs.get("user_document"),
            "usuario_telefono": kwargs.get("user_phone"),
            "usuario_ciudad": kwargs.get("city"),
            "usuario_departamento": kwargs.get("department"),
            "usuario_direccion": kwargs.get("address"),
            "categoria": kwargs["category"],
            "workflow_type": kwargs["workflow_type"],
            "descripcion": kwargs["description"],
            "recommended_action": kwargs["recommended_action"],
            "strategy_text": kwargs.get("strategy_text"),
            "facts": kwargs.get("facts") or {},
            "legal_analysis": kwargs.get("legal_analysis") or {},
            "routing": kwargs.get("routing") or {},
            "prerequisites": kwargs.get("prerequisites") or [],
            "warnings": kwargs.get("warnings") or [],
            "estado": "borrador",
            "payment_status": "pendiente",
            "payment_reference": None,
            "generated_document": None,
            "submission_summary": {},
            "attachments": list(kwargs.get("attachment_ids") or []),
            "created_at": created_at,
            "updated_at": created_at,
        }
        self.cases[case_id] = case
        self.events[case_id] = []
        self.files_by_case[case_id] = []
        self.submission_attempts[case_id] = []
        self.payment_orders[case_id] = []
        return case

    def attach_files_to_case(self, case_id: str, user_id: str, attachment_ids: list[str]) -> list[dict[str, Any]]:
        return []

    def update_file_location(self, file_id: str, **kwargs: Any) -> None:
        return None

    def create_event(
        self,
        *,
        case_id: str,
        event_type: str,
        actor_type: str,
        actor_id: str | None,
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        self.event_counter += 1
        event = {
            "id": str(self.event_counter),
            "event_type": event_type,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "payload": payload or {},
            "created_at": _now(),
        }
        self.events.setdefault(case_id, []).append(event)
        return event

    def get_case_for_user(self, case_id: str, user_id: str) -> dict[str, Any] | None:
        case = self.cases.get(str(case_id))
        if not case or str(case.get("user_id")) != str(user_id):
            return None
        return case

    def list_files_for_case(self, case_id: str) -> list[dict[str, Any]]:
        return list(self.files_by_case.get(str(case_id), []))

    def update_case_intake(
        self,
        case_id: str,
        *,
        workflow_type: str,
        description: str,
        facts: dict[str, Any],
        legal_analysis: dict[str, Any],
        routing: dict[str, Any],
        prerequisites: list[dict[str, Any]],
        warnings: list[str],
        recommended_action: str,
        strategy_text: str,
    ) -> dict[str, Any] | None:
        case = self.cases.get(str(case_id))
        if not case:
            return None
        case.update(
            {
                "workflow_type": workflow_type,
                "descripcion": description,
                "facts": facts,
                "legal_analysis": legal_analysis,
                "routing": routing,
                "prerequisites": prerequisites,
                "warnings": warnings,
                "recommended_action": recommended_action,
                "strategy_text": strategy_text,
                "updated_at": _now(),
            }
        )
        return case

    def list_payment_orders_for_case(self, case_id: str) -> list[dict[str, Any]]:
        orders = list(self.payment_orders.get(str(case_id), []))
        return sorted(orders, key=lambda item: item["created_at"], reverse=True)

    def update_case_payment(
        self,
        case_id: str,
        reference: str,
        *,
        payment_status: str = "pagado",
    ) -> dict[str, Any] | None:
        case = self.cases.get(str(case_id))
        if not case:
            return None
        case["payment_reference"] = reference
        case["payment_status"] = payment_status
        case["updated_at"] = _now()
        return case

    def list_submission_attempts(self, case_id: str) -> list[dict[str, Any]]:
        return list(self.submission_attempts.get(str(case_id), []))

    def create_submission_attempt(
        self,
        *,
        case_id: str,
        channel: str,
        destination_name: str | None,
        destination_contact: str | None,
        subject: str | None,
        cc: list[str] | None,
        status: str,
        radicado: str | None,
        response_payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        self.submission_counter += 1
        created_at = _now()
        attempt = {
            "id": str(self.submission_counter),
            "channel": channel,
            "destination_name": destination_name,
            "destination_contact": destination_contact,
            "subject": subject,
            "cc": list(cc or []),
            "status": status,
            "radicado": radicado,
            "response_payload": response_payload or {},
            "error_text": None,
            "created_at": created_at,
            "updated_at": created_at,
        }
        self.submission_attempts.setdefault(str(case_id), []).append(attempt)
        return attempt

    def list_case_events(self, case_id: str) -> list[dict[str, Any]]:
        return list(self.events.get(str(case_id), []))

    def update_case_document(self, case_id: str, document: str) -> dict[str, Any] | None:
        case = self.cases.get(str(case_id))
        if not case:
            return None
        case["generated_document"] = document
        case["updated_at"] = _now()
        return case

    def update_case_status(
        self,
        case_id: str,
        *,
        status: str,
        submission_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        case = self.cases.get(str(case_id))
        if not case:
            return None
        case["estado"] = status
        if submission_summary is not None:
            case["submission_summary"] = submission_summary
        case["updated_at"] = _now()
        return case

    def update_case_submission(
        self,
        case_id: str,
        *,
        status: str,
        manual_contact: dict[str, Any] | None = None,
        submission_summary: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        case = self.cases.get(str(case_id))
        if not case:
            return None
        case["estado"] = status
        case["manual_contact"] = manual_contact or {}
        if submission_summary is not None:
            case["submission_summary"] = submission_summary
        case["updated_at"] = _now()
        return case


TEST_USER = {
    "id": "user-health-smoke",
    "name": "Maria Fernanda Lopez",
    "email": "maria.salud@example.com",
    "document_number": "1032456789",
    "phone": "3001234567",
    "city": "Bogota",
    "department": "Cundinamarca",
    "address": "Calle 100 # 10-20",
    "role": "citizen",
}


CASES: list[HealthFlowCase] = [
    HealthFlowCase(
        name="flujo_tutela_continuidad",
        description=(
            "Mi hijo menor necesita continuidad inmediata de quimioterapia. "
            "La EPS dejo vencer la autorizacion y ya perdio una sesion."
        ),
        category="Salud",
        city="Bogota",
        department="Cundinamarca",
        prior_actions=["eps_pqrs"],
        create_form={
            "target_entity": "Nueva EPS",
            "eps_name": "Nueva EPS",
            "acting_capacity": "madre_padre_menor",
            "represented_person_name": "Samuel Perez Lopez",
            "represented_person_age": "8 anos",
            "represented_person_document": "TI 100200300",
            "diagnosis": "Leucemia linfoblastica aguda",
            "treatment_needed": "Continuidad inmediata de quimioterapia pediatrica ordenada por oncologia",
            "key_dates": "2026-03-10 orden medica, 2026-03-11 solicitud a EPS, 2026-03-13 sesion perdida",
            "urgency_detail": "La suspension del tratamiento aumenta el riesgo de recaida y complicaciones graves.",
            "ongoing_harm": "Ya perdio una sesion programada y sigue sin autorizacion vigente.",
            "special_protection": "Menor de edad",
            "tutela_special_protection_detail": "Es un menor con cancer y tratamiento continuo que no puede interrumpirse.",
            "medical_order_date": "2026-03-10",
            "treating_doctor_name": "Dra. Laura Gomez",
            "evidence_summary": "Orden de quimioterapia, historia clinica y autorizacion vencida.",
            "eps_request_date": "2026-03-11",
            "eps_response_detail": "La EPS dejo vencer la autorizacion y no reagendo la sesion.",
            "prior_claim": "si",
            "prior_claim_result": "Se radico solicitud y la EPS no resolvio antes de la fecha programada.",
            "tutela_previous_action_detail": "No existe otra tutela previa por estos mismos hechos.",
            "tutela_oath_statement": "Bajo juramento manifiesto que no he presentado otra tutela por estos mismos hechos.",
            "case_story": "La EPS interrumpio la quimioterapia de un menor con leucemia por una autorizacion vencida.",
            "concrete_request": "Ordenar la continuidad inmediata del tratamiento oncologico sin nuevas barreras.",
        },
        intake_update_form={
            "tutela_other_means_detail": "La familia radico solicitud, pero la continuidad no puede esperar otra respuesta administrativa.",
            "tutela_immediacy_detail": "La interrupcion es actual porque el tratamiento ya se suspendio esta semana.",
            "tutela_previous_action_detail": "No existe otra tutela previa por estos mismos hechos.",
            "tutela_oath_statement": "Bajo juramento manifiesto que no he presentado otra tutela por estos mismos hechos.",
        },
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        attachment_names=["Historia Clinica Samuel Perez.pdf", "Orden Quimioterapia.pdf"],
    ),
    HealthFlowCase(
        name="flujo_peticion_salud",
        description=(
            "Solicito que la EPS entregue copia de una autorizacion y reprograme una cita con ortopedia. "
            "No es una urgencia vital, pero llevo semanas sin respuesta y requiero informacion clara sobre la fecha de atencion."
        ),
        category="Salud",
        city="Bogota",
        department="Cundinamarca",
        prior_actions=["eps_pqrs"],
        create_form={
            "target_entity": "Sanitas EPS",
            "eps_name": "Sanitas EPS",
            "acting_capacity": "nombre_propio",
            "diagnosis": "Dolor lumbar cronico",
            "treatment_needed": "Reprogramacion de cita con ortopedia y entrega de copia de autorizacion",
            "key_dates": "2026-02-20 orden medica, 2026-03-01 solicitud previa sin respuesta",
            "urgency_detail": "La afectacion existe, pero no hay un riesgo vital inmediato.",
            "medical_order_date": "2026-02-20",
            "treating_doctor_name": "Dra. Paula Medina",
            "evidence_summary": "Orden medica y solicitud previa.",
            "prior_claim": "si",
            "prior_claim_result": "La EPS no responde de fondo desde hace varias semanas.",
            "case_story": (
                "Desde febrero solicite a la EPS copia de la autorizacion y la reprogramacion de una cita con ortopedia. "
                "La entidad no ha dado respuesta clara, sigo sin fecha asignada y necesito esa informacion para continuar mi manejo."
            ),
            "concrete_request": "Responder de fondo y reprogramar la cita.",
            "numbered_requests": "1. Entregar copia de la autorizacion. 2. Reprogramar la cita con ortopedia. 3. Informar fecha cierta de atencion.",
            "response_channel": "Correo electronico",
        },
        intake_update_form={
            "numbered_requests": "1. Entregar copia de la autorizacion. 2. Reprogramar la cita con ortopedia.",
            "response_channel": "Correo electronico",
        },
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        expected_generate_error="Todavia faltan datos minimos para generar este documento",
        attachment_names=None,
    ),
    HealthFlowCase(
        name="flujo_impugnacion_salud",
        description=(
            "Impugno el fallo de tutela del Juzgado 8 Penal Municipal de Bogota. La fecha del fallo o decision de tutela "
            "fue el 5 de marzo de 2026 y el resultado de la decision de tutela fue negada. "
            "Los motivos de impugnacion son el error de valoracion y la omision de la historia clinica y del riesgo actual "
            "por suspender el tratamiento neurologico."
        ),
        category="Salud",
        city="Bogota",
        department="Cundinamarca",
        prior_actions=[],
        create_form={
            "target_entity": "Famisanar EPS",
            "eps_name": "Famisanar EPS",
            "acting_capacity": "nombre_propio",
            "diagnosis": "Esclerosis multiple",
            "treatment_needed": "Continuidad de medicamento inmunomodulador formulado por neurologia",
            "key_dates": "2026-03-05 fallo de tutela negado, 2026-03-06 notificacion",
            "urgency_detail": "La suspension del medicamento aumenta el riesgo de recaidas neurologicas y perdida funcional.",
            "ongoing_harm": "Sigo sin acceso al tratamiento pese al fallo adverso.",
            "medical_order_date": "2026-02-28",
            "treating_doctor_name": "Dr. Juan Carlos Romero",
            "evidence_summary": "Fallo de tutela, historia clinica y orden medica de continuidad.",
            "tutela_court_name": "Juzgado 8 Penal Municipal de Bogota",
            "tutela_ruling_date": "2026-03-05",
            "tutela_decision_result": "Tutela negada por supuesta falta de urgencia",
            "tutela_appeal_reason": "El fallo omitio valorar la orden medica, la historia clinica y el riesgo actual por interrumpir el tratamiento.",
            "case_story": "El juzgado nego la tutela en salud sin valorar la prueba medica clave ni el riesgo actual de la paciente.",
            "concrete_request": "Revocar el fallo y conceder la tutela para ordenar la continuidad inmediata del tratamiento.",
        },
        intake_update_form={
            "tutela_appeal_reason": "El fallo desconoce la historia clinica, la orden vigente y el dano actual por suspender el medicamento.",
            "concrete_request": "Revocar la decision impugnada y ordenar la entrega inmediata del tratamiento neurologico formulado.",
        },
        expected_workflow="impugnacion",
        expected_action="Impugnacion de tutela",
        expected_generate_error="Todavia faltan datos minimos para generar este documento",
        attachment_names=["Historia Clinica Neurologia.pdf", "Fallo Tutela.pdf"],
    ),
    HealthFlowCase(
        name="flujo_desacato_salud",
        description=(
            "Promuevo incidente de desacato por incumplimiento de fallo de tutela. El Juzgado 12 Civil Municipal de Bogota "
            "emitio el fallo y orden judicial el 1 de marzo de 2026, con entrega del medicamento en 48 horas. "
            "La EPS fue notificada y hoy persiste el incumplimiento actual de la orden judicial."
        ),
        category="Salud",
        city="Bogota",
        department="Cundinamarca",
        prior_actions=[],
        create_form={
            "target_entity": "Compensar EPS",
            "eps_name": "Compensar EPS",
            "acting_capacity": "nombre_propio",
            "diagnosis": "Artritis reumatoide severa",
            "treatment_needed": "Entrega inmediata de medicamento biologico ordenado",
            "key_dates": "2026-03-01 fallo favorable, 2026-03-03 vencio plazo de 48 horas",
            "urgency_detail": "La falta del medicamento mantiene dolor intenso, inflamacion y deterioro funcional.",
            "ongoing_harm": "La EPS sigue sin entregar el medicamento pese a la orden judicial.",
            "medical_order_date": "2026-02-25",
            "treating_doctor_name": "Dra. Andrea Pardo",
            "evidence_summary": "Fallo de tutela, constancia de notificacion y formula del medicamento.",
            "tutela_court_name": "Juzgado 12 Civil Municipal de Bogota",
            "tutela_ruling_date": "2026-03-01",
            "tutela_order_summary": "Ordeno entregar el medicamento biologico en 48 horas",
            "tutela_noncompliance_detail": "Han pasado varios dias desde la notificacion y la EPS sigue incumpliendo la orden.",
            "case_story": "Existe fallo favorable y la EPS no ha cumplido la orden de entregar el medicamento formulado.",
            "concrete_request": "Abrir incidente de desacato y ordenar el cumplimiento inmediato del fallo.",
        },
        intake_update_form={
            "tutela_noncompliance_detail": "La EPS fue notificada, vencio el plazo judicial y hoy persiste el incumplimiento con afectacion actual en salud.",
            "concrete_request": "Tramitar desacato y ordenar la entrega inmediata del medicamento biologico ordenado por el juzgado.",
        },
        expected_workflow="desacato",
        expected_action="Incidente de desacato",
        expected_generate_error="Todavia faltan datos minimos para generar este documento",
        attachment_names=["Historia Clinica Artritis.pdf", "Fallo Tutela.pdf"],
    ),
    HealthFlowCase(
        name="bloqueo_generate_tutela_incompleta",
        description=(
            "Mi EPS demora una cita prioritaria y sigo afectada, por eso necesito una tutela en salud. "
            "La situacion me preocupa, pero todavia no he completado varios datos juridicos de cierre."
        ),
        category="Salud",
        city="Bogota",
        department="Cundinamarca",
        prior_actions=["eps_pqrs"],
        create_form={
            "target_entity": "Sura EPS",
            "eps_name": "Sura EPS",
            "acting_capacity": "nombre_propio",
            "diagnosis": "Dolor abdominal recurrente",
            "treatment_needed": "Cita prioritaria con gastroenterologia y ayudas diagnosticas",
            "key_dates": "2026-03-12 orden medica, 2026-03-14 solicitud a EPS",
            "urgency_detail": "El dolor sigue y la EPS no asigna la cita prioritaria.",
            "ongoing_harm": "Persisten sintomas y no hay fecha de atencion.",
            "medical_order_date": "2026-03-12",
            "treating_doctor_name": "Dr. Felipe Moreno",
            "evidence_summary": "Orden medica y captura de solicitud a la EPS.",
            "prior_claim": "si",
            "prior_claim_result": "Se solicito la cita, pero la EPS no define fecha de atencion.",
            "tutela_oath_statement": "Bajo juramento manifiesto que no he presentado otra tutela por estos mismos hechos.",
            "case_story": "La EPS demora una cita prioritaria y los examenes ordenados pese a dolor persistente.",
            "concrete_request": "Ordenar la asignacion inmediata de la cita prioritaria y de los examenes formulados.",
        },
        intake_update_form={},
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        expected_generate_error="Todavia faltan datos minimos para generar este documento",
    ),
]


def _build_form(case: HealthFlowCase) -> dict[str, Any]:
    merged = dict(case.create_form)
    merged.update(case.intake_update_form)
    return merged


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_smoke_attachment(case_name: str, original_name: str, index: int) -> str:
    root = ensure_upload_root() / "health_smoke"
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"{case_name}_{index}.txt"
    lowered_case = case_name.lower()
    lowered_name = original_name.lower()
    if "peticion" in lowered_case:
        content = (
            "Historia clinica. Consulta externa del 20/02/2026. "
            "Paciente con dolor lumbar cronico y orden de ortopedia. "
            "Se solicita reprogramacion de cita y copia de autorizacion. "
            "No hay riesgo vital inmediato y el manejo es ambulatorio."
        )
    elif "orden" in lowered_name or "quimioterapia" in lowered_name:
        content = (
            "Orden medica del 10/03/2026. Servicio requerido: continuidad inmediata de tratamiento formulado. "
            "La EPS no puede suspender ni demorar la autorizacion."
        )
    else:
        content = (
            "Historia clinica. Consulta del 16/03/2026 en Comfama Itagui. "
            "Paciente con diagnostico principal, barrera de acceso actual y necesidad de atencion prioritaria. "
            "Medicina interna, endocrinologia y teleconcepto hacen parte del recorrido clinico. "
            "La EPS mantiene demora o remision interna sin solucion definitiva."
        )
    target.write_text(
        content,
        encoding="utf-8",
    )
    return target.relative_to(ensure_upload_root()).as_posix()


def _run_case(case: HealthFlowCase) -> str:
    create_payload = CaseCreateRequest(
        category=case.category,
        department=case.department,
        city=case.city,
        description=case.description,
        prior_actions=case.prior_actions,
        form_data=case.create_form,
        attachment_ids=[],
    )
    created = app_v2.create_case(create_payload, current_user=TEST_USER)
    created_case = created.case
    if case.attachment_names:
        app_v2.repository.files_by_case[str(created_case.id)] = [
            {
                "id": f"{case.name}-{index}",
                "case_id": str(created_case.id),
                "original_name": name,
                "file_kind": "evidence",
                "mime_type": "application/pdf",
                "relative_path": _write_smoke_attachment(case.name, name, index),
                "status": "attached",
                "file_size": 1024,
                "created_at": _now(),
                "metadata": {},
            }
            for index, name in enumerate(case.attachment_names, start=1)
        ]
    _assert(created_case.workflow_type == case.expected_workflow, f"{case.name}: workflow inesperado en create_case")
    _assert(created_case.recommended_action == case.expected_action, f"{case.name}: accion inesperada en create_case")

    update_payload = CaseIntakeUpdateRequest(description=case.description, form_data=_build_form(case))
    updated = app_v2.update_case_intake(str(created_case.id), update_payload, current_user=TEST_USER)
    updated_case = updated.case
    _assert(updated_case.workflow_type == case.expected_workflow, f"{case.name}: workflow inesperado en update_case_intake")
    _assert(updated_case.recommended_action == case.expected_action, f"{case.name}: accion inesperada en update_case_intake")

    paid = app_v2.repository.update_case_payment(str(created_case.id), reference=f"SMOKE-{case.name.upper()}")
    _assert(bool(paid), f"{case.name}: no fue posible simular pago")

    try:
        generated = app_v2.generate_document(str(created_case.id), payload=None, current_user=TEST_USER)
    except HTTPException as exc:
        if case.expected_generate_error:
            _assert(exc.status_code == 422, f"{case.name}: status inesperado en bloqueo de generate")
            _assert(case.expected_generate_error in str(exc.detail), f"{case.name}: detalle inesperado en bloqueo de generate")
            return f"{case.name}: bloqueo esperado en generate -> OK"
        raise

    if case.expected_generate_error:
        raise AssertionError(f"{case.name}: generate_document debio bloquearse y no lo hizo")

    _assert(bool(generated.document.strip()), f"{case.name}: documento vacio")
    _assert(generated.case.payment_status == "pagado", f"{case.name}: payment_status inesperado")
    _assert(bool(generated.case.generated_document), f"{case.name}: no quedo persistido el documento")
    _assert(generated.quality_review.get("passed") is True, f"{case.name}: quality review no paso")
    return f"{case.name}: {generated.case.recommended_action} -> OK ({len(generated.document.split())} palabras)"


def main() -> int:
    original_repository = app_v2.repository
    original_workflows_repository = workflows.repository
    app_v2.repository = InMemoryRepository()
    workflows.repository = app_v2.repository
    try:
        outputs: list[str] = []
        for case in CASES:
            outputs.append(_run_case(case))
    except HTTPException as exc:
        print(f"Fallo HTTP {exc.status_code}: {exc.detail}")
        return 1
    except Exception as exc:
        print(f"Fallo: {exc}")
        return 1
    finally:
        app_v2.repository = original_repository
        workflows.repository = original_workflows_repository

    for line in outputs:
        print(line)
    print(f"Resultado: {len(outputs)} flujo(s) reales validados correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
