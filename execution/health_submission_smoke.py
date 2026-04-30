from __future__ import annotations

from pathlib import Path
import sys

from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import app_v2, workflows
from backend.schemas_v2 import CaseIntakeUpdateRequest, CaseSubmitRequest
from execution.health_flow_smoke import CASES, InMemoryRepository, TEST_USER, HealthFlowCase, _now, _write_smoke_attachment

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


def _get_case(case_name: str) -> HealthFlowCase:
    for case in CASES:
        if case.name == case_name:
            return case
    raise ValueError(f"Caso no encontrado en health_flow_smoke: {case_name}")


def _prepare_case(case_name: str) -> str:
    case = _get_case(case_name)
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
    if case.attachment_names:
        app_v2.repository.files_by_case[str(created.case.id)] = [
            {
                "id": f"{case.name}-{index}",
                "case_id": str(created.case.id),
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
    update_payload = CaseIntakeUpdateRequest(description=case.description, form_data={**case.create_form, **case.intake_update_form})
    app_v2.update_case_intake(str(created.case.id), update_payload, current_user=TEST_USER)
    app_v2.repository.update_case_payment(str(created.case.id), reference=f"SUBMIT-{case.name.upper()}")
    app_v2.repository.payment_orders.setdefault(str(created.case.id), []).append(
        {
            "reference": f"SUBMIT-{case.name.upper()}",
            "status": "approved",
            "product_code": "salud_tutela",
            "include_filing": True,
            "created_at": _now(),
        }
    )
    app_v2.generate_document(str(created.case.id), payload=None, current_user=TEST_USER)
    return str(created.case.id)


def main() -> int:
    original_repository = app_v2.repository
    original_workflows_repository = workflows.repository
    repo = InMemoryRepository()
    app_v2.repository = repo
    workflows.repository = repo
    try:
        tutela_case_id = _prepare_case("flujo_tutela_continuidad")
        tutela_auto = app_v2.submit_case(
            tutela_case_id,
            CaseSubmitRequest(
                mode="auto",
                notes="Smoke submit tutela auto",
                judicial_destination_confirmed=True,
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

    except HTTPException as exc:
        print(f"Fallo HTTP {exc.status_code}: {exc.detail}")
        return 1
    except Exception as exc:
        print(f"Fallo: {exc}")
        return 1
    finally:
        app_v2.repository = original_repository
        workflows.repository = original_workflows_repository

    print("tutela_salud_auto: OK")
    print("Resultado: 1 politica(s) de radicacion validadas correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
