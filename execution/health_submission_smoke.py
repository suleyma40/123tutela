from __future__ import annotations

from pathlib import Path
import sys

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import app_v2, workflows
from backend.schemas_v2 import CaseIntakeUpdateRequest, CaseSubmitRequest
from execution.health_flow_smoke import CASES, InMemoryRepository, TEST_USER

CONSENT_TEXT = (
    "Autorizo a 123tutela para usar mi firma electronica simple en la radicacion o envio del documento generado para este caso. "
    "Confirmo que revise el contenido final antes de aceptarlo, que los datos de identificacion y ciudad que suministro son correctos, "
    "y que esta aceptacion expresa representa mi voluntad de presentar este documento por medios electronicos en el canal aplicable. "
    "Entiendo que la plataforma conservara evidencia basica de esta aceptacion, incluida la fecha y hora, la version del consentimiento "
    "y metadatos tecnicos del envio disponibles en el sistema."
)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _prepare_case(case_index: int) -> str:
    case = CASES[case_index]
    create_payload = app_v2.CaseCreateRequest(
        category=case.category,
        department=case.department,
        city=case.city,
        description=case.description,
        prior_actions=case.prior_actions,
        form_data=case.create_form,
        attachment_ids=[],
    )
    created = app_v2.create_case(create_payload, current_user=TEST_USER)
    update_payload = CaseIntakeUpdateRequest(description=case.description, form_data={**case.create_form, **case.intake_update_form})
    app_v2.update_case_intake(str(created.case.id), update_payload, current_user=TEST_USER)
    app_v2.repository.update_case_payment(str(created.case.id), reference=f"SUBMIT-{case.name.upper()}")
    app_v2.generate_document(str(created.case.id), payload=None, current_user=TEST_USER)
    return str(created.case.id)


def main() -> int:
    original_repository = app_v2.repository
    original_workflows_repository = workflows.repository
    repo = InMemoryRepository()
    app_v2.repository = repo
    workflows.repository = repo
    try:
        petition_case_id = _prepare_case(1)
        petition_result = app_v2.submit_case(
            petition_case_id,
            CaseSubmitRequest(
                mode="auto",
                notes="Smoke submit petition",
                signature={
                    "full_name": TEST_USER["name"],
                    "document_number": TEST_USER["document_number"],
                    "city": TEST_USER["city"],
                    "date": "2026-03-19",
                    "accepted": True,
                    "consent_version": "ses_v1",
                    "consent_text": CONSENT_TEXT,
                },
                reviewed_document=True,
            ),
            current_user=TEST_USER,
        )
        petition_summary = petition_result.case.submission_summary
        _assert((petition_summary.get("submission_policy") or {}).get("preferred_mode") == "auto", "peticion: policy inesperada")
        _assert(petition_result.case.status in {"enviado", "radicado"}, "peticion: status inesperado")

        tutela_case_id = _prepare_case(0)
        tutela_auto = app_v2.submit_case(
            tutela_case_id,
            CaseSubmitRequest(
                mode="auto",
                notes="Smoke submit tutela auto",
                signature={
                    "full_name": TEST_USER["name"],
                    "document_number": TEST_USER["document_number"],
                    "city": TEST_USER["city"],
                    "date": "2026-03-19",
                    "accepted": True,
                    "consent_version": "ses_v1",
                    "consent_text": CONSENT_TEXT,
                },
                reviewed_document=True,
            ),
            current_user=TEST_USER,
        )
        tutela_policy = tutela_auto.case.submission_summary.get("submission_policy") or {}
        _assert(tutela_policy.get("preferred_mode") == "auto", "tutela: preferred_mode inesperado")
        _assert(tutela_auto.case.status in {"enviado", "radicado"}, "tutela: status inesperado para auto")

        impugnacion_case_id = _prepare_case(2)
        impugnacion_auto = app_v2.submit_case(
            impugnacion_case_id,
            CaseSubmitRequest(
                mode="auto",
                notes="Smoke submit impugnacion auto",
                signature={
                    "full_name": TEST_USER["name"],
                    "document_number": TEST_USER["document_number"],
                    "city": TEST_USER["city"],
                    "date": "2026-03-19",
                    "accepted": True,
                    "consent_version": "ses_v1",
                    "consent_text": CONSENT_TEXT,
                },
                reviewed_document=True,
            ),
            current_user=TEST_USER,
        )
        _assert((impugnacion_auto.case.submission_summary.get("submission_policy") or {}).get("preferred_mode") == "auto", "impugnacion: preferred_mode inesperado")
        _assert(impugnacion_auto.case.status in {"enviado", "radicado"}, "impugnacion: status inesperado para auto")

        desacato_case_id = _prepare_case(3)
        desacato_auto = app_v2.submit_case(
            desacato_case_id,
            CaseSubmitRequest(
                mode="auto",
                notes="Smoke submit desacato auto",
                signature={
                    "full_name": TEST_USER["name"],
                    "document_number": TEST_USER["document_number"],
                    "city": TEST_USER["city"],
                    "date": "2026-03-19",
                    "accepted": True,
                    "consent_version": "ses_v1",
                    "consent_text": CONSENT_TEXT,
                },
                reviewed_document=True,
            ),
            current_user=TEST_USER,
        )
        _assert((desacato_auto.case.submission_summary.get("submission_policy") or {}).get("preferred_mode") == "auto", "desacato: preferred_mode inesperado")
        _assert(desacato_auto.case.status in {"enviado", "radicado"}, "desacato: status inesperado para auto")

    except HTTPException as exc:
        print(f"Fallo HTTP {exc.status_code}: {exc.detail}")
        return 1
    except Exception as exc:
        print(f"Fallo: {exc}")
        return 1
    finally:
        app_v2.repository = original_repository
        workflows.repository = original_workflows_repository

    print("peticion_salud_auto: OK")
    print("tutela_salud_auto: OK")
    print("impugnacion_salud_auto: OK")
    print("desacato_salud_auto: OK")
    print("Resultado: 4 politica(s) de radicacion validadas correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
