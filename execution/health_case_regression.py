from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.agent_orchestrator import build_health_agent_state
from backend.case_architecture import evaluate_tutela_procedencia
from backend.intake_validation_v2 import validate_submission_readiness
from backend.workflows import infer_workflow


@dataclass(frozen=True)
class HealthRegressionCase:
    name: str
    description: str
    facts: dict[str, Any]
    prior_actions: list[str]
    expected_workflow: str
    expected_action: str
    expected_preview_status: str
    expect_agent_enabled: bool = True
    expect_tutela_procedencia: str | None = None


def _base_facts(intake_form: dict[str, Any], *, problem: str = "salud", dates: str = "") -> dict[str, Any]:
    entities = []
    target = str(intake_form.get("target_entity") or intake_form.get("eps_name") or "").strip()
    if target:
        entities.append(target)
    return {
        "problema_central": problem,
        "hechos_principales": intake_form.get("case_story") or "",
        "fechas_mencionadas": dates or intake_form.get("key_dates") or "",
        "entidades_involucradas": entities,
        "intake_form": intake_form,
        "attachment_intelligence": {},
        "uploaded_evidence_files": [],
    }


def _with_judicial_ruling_attachment(
    facts: dict[str, Any],
    *,
    filename: str,
    court_name: str,
    ruling_date: str,
    decision_result: str = "",
    order_summary: str = "",
) -> dict[str, Any]:
    enriched = dict(facts)
    enriched["uploaded_evidence_files"] = [filename]
    enriched["attachment_intelligence"] = {
        "profiles": [{"type": "fallo_tutela", "original_name": filename}],
        "judicial_ruling_analysis": {
            "attachment_present": True,
            "attachments_count": 1,
            "source_name": filename,
            "court_name": court_name,
            "ruling_date": ruling_date,
            "decision_result": decision_result,
            "order_summary": order_summary,
            "analysis_ready": True,
        },
    }
    return enriched


CASES: list[HealthRegressionCase] = [
    HealthRegressionCase(
        name="continuidad_tratamiento",
        description=(
            "Mi hijo de 8 anos con leucemia necesita quimioterapia continua. "
            "Nueva EPS dejo vencer la autorizacion y ya perdio una sesion. "
            "La oncologa advirtio que no se puede interrumpir el tratamiento."
        ),
        facts=_base_facts(
            {
                "target_entity": "Nueva EPS",
                "eps_name": "Nueva EPS",
                "acting_capacity": "madre_padre_menor",
                "represented_person_name": "Samuel Perez Lopez",
                "represented_person_age": "8 anos",
                "represented_person_document": "TI 100200300",
                "diagnosis": "Leucemia linfoblastica aguda",
                "treatment_needed": "Continuidad inmediata de quimioterapia programada por oncologia pediatrica",
                "urgency_detail": "La suspension del tratamiento aumenta el riesgo de recaida y complicaciones graves.",
                "ongoing_harm": "Ya perdio una sesion y el nino sigue sin tratamiento continuo.",
                "special_protection": "Menor de edad",
                "tutela_special_protection_detail": "Es un menor con cancer y tratamiento continuo que no puede interrumpirse.",
                "medical_order_date": "2026-03-10",
                "treating_doctor_name": "Dra. Laura Gomez",
                "evidence_summary": "Orden de quimioterapia, historia clinica y autorizacion vencida.",
                "eps_request_date": "2026-03-11",
                "eps_response_detail": "La EPS dejo vencer la autorizacion y no reagendo la sesion.",
                "prior_claim": "si",
                "prior_claim_result": "Se radico solicitud y la EPS no resolvio antes de la fecha programada.",
                "tutela_other_means_detail": "La familia radico solicitud, pero la continuidad no puede esperar otra respuesta administrativa.",
                "tutela_immediacy_detail": "La interrupcion es actual porque el tratamiento ya se suspendio esta semana.",
                "tutela_previous_action_detail": "No existe otra tutela previa por estos mismos hechos.",
                "tutela_oath_statement": "Bajo juramento manifiesto que no he presentado otra tutela por estos mismos hechos.",
                "case_story": "La EPS interrumpio la quimioterapia de un menor con leucemia por una autorizacion vencida.",
                "concrete_request": "Ordenar la continuidad inmediata del tratamiento oncologico sin nuevas barreras.",
            },
            dates="2026-03-11, 2026-03-13",
        ),
        prior_actions=["eps_pqrs"],
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        expected_preview_status="ok",
        expect_tutela_procedencia="alta",
    ),
    HealthRegressionCase(
        name="embarazo_alto_riesgo_sin_pqrs_cerrada",
        description=(
            "Estoy embarazada y mi medico ordeno una ecografia de alto riesgo y control prioritario. "
            "La EPS sigue demorando la autorizacion y tengo dolor y sangrado intermitente."
        ),
        facts=_base_facts(
            {
                "target_entity": "Sura EPS",
                "eps_name": "Sura EPS",
                "acting_capacity": "nombre_propio",
                "diagnosis": "Embarazo de alto riesgo",
                "treatment_needed": "Ecografia obstetrica de alto riesgo y control prioritario por medicina materno fetal",
                "urgency_detail": "Hay dolor y sangrado intermitente, por lo que no puedo esperar semanas a otra respuesta.",
                "special_protection": "Embarazada",
                "tutela_special_protection_detail": "El embarazo es de alto riesgo y la demora puede afectar mi salud y la del bebe.",
                "medical_order_date": "2026-03-15",
                "treating_doctor_name": "Dr. Felipe Rojas",
                "evidence_summary": "Orden medica y resumen de urgencias.",
                "prior_claim": "si",
                "eps_response_detail": "La EPS no ha autorizado el control prioritario y sigue aplazando la gestion.",
                "prior_claim_result": "Se solicito autorizacion prioritaria y la EPS sigue demorando la respuesta.",
                "tutela_other_means_detail": "No alcanzo a esperar una PQRS completa porque el riesgo es actual.",
                "tutela_immediacy_detail": "La vulneracion es actual porque la cita de alto riesgo debia autorizarse de inmediato.",
                "tutela_previous_action_detail": "No existe tutela previa.",
                "tutela_oath_statement": "No he presentado otra tutela por estos hechos.",
                "case_story": "La EPS demora atencion prioritaria para embarazo de alto riesgo con sangrado intermitente.",
                "concrete_request": "Ordenar autorizacion inmediata de ecografia y control prioritario.",
            },
            dates="2026-03-15",
        ),
        prior_actions=[],
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        expected_preview_status="ok",
        expect_tutela_procedencia="alta",
    ),
    HealthRegressionCase(
        name="peticion_salud_ordinaria",
        description=(
            "Necesito que la EPS me entregue copia de una autorizacion y me reprograme una cita con especialista. "
            "No es una urgencia vital, pero ya llevo varias semanas esperando respuesta."
        ),
        facts=_base_facts(
            {
                "target_entity": "Sanitas EPS",
                "eps_name": "Sanitas EPS",
                "acting_capacity": "nombre_propio",
                "diagnosis": "Dolor lumbar cronico",
                "treatment_needed": "Reprogramacion de cita con ortopedia y entrega de copia de autorizacion",
                "urgency_detail": "La afectacion existe, pero no hay un riesgo vital inmediato.",
                "medical_order_date": "2026-02-20",
                "treating_doctor_name": "Dra. Paula Medina",
                "evidence_summary": "Orden medica y solicitud previa.",
                "prior_claim": "si",
                "prior_claim_result": "La EPS no responde de fondo desde hace varias semanas.",
                "case_story": "La EPS no entrega copia de autorizacion ni reprograme una cita pendiente.",
                "concrete_request": "Responder de fondo y reprogramar la cita.",
                "numbered_requests": "1. Entregar copia de la autorizacion. 2. Reprogramar la cita con ortopedia.",
                "response_channel": "Correo electronico",
            },
            dates="2026-02-20, 2026-03-01",
        ),
        prior_actions=["eps_pqrs"],
        expected_workflow="derecho_peticion",
        expected_action="Derecho de peticion a EPS",
        expected_preview_status="ok",
    ),
    HealthRegressionCase(
        name="desacato_salud",
        description=(
            "El juzgado concedio la tutela, ordeno entregar el medicamento en 48 horas y la EPS sigue sin cumplir."
        ),
        facts=_with_judicial_ruling_attachment(
            _base_facts(
                {
                    "target_entity": "Compensar EPS",
                    "eps_name": "Compensar EPS",
                    "diagnosis": "Artritis reumatoide severa",
                    "treatment_needed": "Entrega inmediata de medicamento biologico ordenado",
                    "tutela_court_name": "Juzgado 12 Civil Municipal de Bogota",
                    "tutela_ruling_date": "2026-03-01",
                    "tutela_order_summary": "Ordeno entregar el medicamento en 48 horas",
                    "tutela_noncompliance_detail": "Han pasado varios dias y la EPS sigue sin entregar el medicamento.",
                    "case_story": "Existe fallo favorable pero la EPS sigue incumpliendo la orden.",
                    "concrete_request": "Promover incidente de desacato por incumplimiento del fallo.",
                },
                dates="2026-03-01, 2026-03-07",
            ),
            filename="Fallo tutela favorable Compensar.pdf",
            court_name="Juzgado 12 Civil Municipal de Bogota",
            ruling_date="2026-03-01",
            decision_result="Tutela concedida",
            order_summary="Ordeno entregar el medicamento en 48 horas",
        ),
        prior_actions=[],
        expected_workflow="desacato",
        expected_action="Incidente de desacato",
        expected_preview_status="ok",
    ),
    HealthRegressionCase(
        name="impugnacion_salud",
        description=(
            "El juzgado nego la tutela por considerar que no habia urgencia, "
            "pero omitio valorar la historia clinica y la orden de tratamiento continuo."
        ),
        facts=_with_judicial_ruling_attachment(
            _base_facts(
                {
                    "target_entity": "Famisanar EPS",
                    "eps_name": "Famisanar EPS",
                    "diagnosis": "Esclerosis multiple",
                    "treatment_needed": "Continuidad de medicamento inmunomodulador formulado por neurologia",
                    "tutela_court_name": "Juzgado 8 Penal Municipal de Bogota",
                    "tutela_ruling_date": "2026-03-05",
                    "tutela_decision_result": "Tutela negada por supuesta falta de urgencia",
                    "tutela_appeal_reason": "El fallo omitio la historia clinica, la orden medica y el riesgo por suspender el tratamiento.",
                    "case_story": "Existe fallo adverso de tutela y se necesita controvertir la valoracion probatoria del juez.",
                    "concrete_request": "Impugnar el fallo y revocar la decision que nego la tutela.",
                },
                dates="2026-03-05",
            ),
            filename="Fallo tutela impugnacion Famisanar.pdf",
            court_name="Juzgado 8 Penal Municipal de Bogota",
            ruling_date="2026-03-05",
            decision_result="Tutela negada por supuesta falta de urgencia",
        ),
        prior_actions=[],
        expected_workflow="impugnacion",
        expected_action="Impugnacion de tutela",
        expected_preview_status="ok_with_warnings",
    ),
    HealthRegressionCase(
        name="discapacidad_con_barrera_eps",
        description=(
            "Soy cuidadora de una mujer con discapacidad severa y la EPS suspendio las terapias integrales. "
            "Desde entonces empeoro su movilidad y no puede hacer actividades basicas."
        ),
        facts=_base_facts(
            {
                "target_entity": "Coosalud EPS",
                "eps_name": "Coosalud EPS",
                "acting_capacity": "acudiente",
                "represented_person_name": "Martha Ruiz Gomez",
                "represented_person_age": "42 anos",
                "represented_person_document": "CC 52200111",
                "represented_person_condition": "Discapacidad severa con dependencia funcional",
                "diagnosis": "Paralisis cerebral y discapacidad motora severa",
                "treatment_needed": "Reanudar terapias fisicas, ocupacionales y de lenguaje suspendidas por la EPS",
                "urgency_detail": "La suspension empeora su movilidad y aumenta el riesgo de regresion funcional.",
                "ongoing_harm": "Ya perdio sesiones y hoy no puede hacer actividades basicas sin apoyo.",
                "special_protection": "Discapacidad",
                "tutela_special_protection_detail": "La paciente tiene discapacidad severa y depende de terapias continuas.",
                "medical_order_date": "2026-03-02",
                "treating_doctor_name": "Dra. Lina Cardenas",
                "evidence_summary": "Historia clinica, orden de terapias y constancia de suspension.",
                "prior_claim": "si",
                "prior_claim_result": "La EPS suspendio las terapias y no ha dado respuesta de fondo.",
                "tutela_other_means_detail": "Se reclamo, pero la suspension sigue y la paciente no puede esperar mas.",
                "tutela_immediacy_detail": "La afectacion es actual porque la terapia ya se interrumpio.",
                "tutela_previous_action_detail": "No existe otra tutela previa.",
                "tutela_oath_statement": "No he presentado otra tutela por estos hechos.",
                "case_story": "La EPS suspendio terapias esenciales de una persona con discapacidad severa.",
                "concrete_request": "Ordenar la reanudacion inmediata de las terapias integrales.",
            },
            dates="2026-03-02, 2026-03-08",
        ),
        prior_actions=["eps_pqrs"],
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        expected_preview_status="ok",
        expect_tutela_procedencia="alta",
    ),
    HealthRegressionCase(
        name="contradiccion_fuerte_eps",
        description=(
            "Marque que no hubo reclamo previo, pero en realidad si envie una PQRS a Sura EPS y me respondieron que no habia agenda. "
            "Tambien aparece Nueva EPS en otro campo por error."
        ),
        facts=_base_facts(
            {
                "target_entity": "Nueva EPS",
                "eps_name": "Sura EPS",
                "acting_capacity": "nombre_propio",
                "diagnosis": "Endometriosis severa",
                "treatment_needed": "Cita prioritaria con ginecologia y autorizacion de procedimiento",
                "urgency_detail": "Sigo con dolor intenso y no tengo cita programada.",
                "medical_order_date": "2026-03-06",
                "treating_doctor_name": "Dr. Camilo Suarez",
                "evidence_summary": "Orden medica y respuesta de la EPS.",
                "prior_claim": "no",
                "prior_claim_result": "Se radico PQRS y la EPS dijo que no habia agenda disponible.",
                "case_story": "El expediente quedo con EPS cruzadas y gestion previa contradictoria.",
                "concrete_request": "Corregir la entidad y ordenar la atencion prioritaria.",
            },
            dates="2026-03-06",
        ),
        prior_actions=[],
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        expected_preview_status="requires_more_data",
    ),
    HealthRegressionCase(
        name="hecho_superado_salud",
        description=(
            "La EPS ya autorizo el procedimiento y ya me programaron la cita para esta semana. "
            "Quiero revisar si aun conviene tutela por lo que paso antes."
        ),
        facts=_base_facts(
            {
                "target_entity": "Aliansalud EPS",
                "eps_name": "Aliansalud EPS",
                "acting_capacity": "nombre_propio",
                "diagnosis": "Colelitiasis sintomatica",
                "treatment_needed": "Programacion de cirugia general",
                "urgency_detail": "Ya no hay una urgencia actual porque la EPS ya programo la cirugia.",
                "medical_order_date": "2026-03-01",
                "treating_doctor_name": "Dr. Juan Acosta",
                "evidence_summary": "Orden medica y autorizacion ya emitida.",
                "prior_claim": "si",
                "prior_claim_result": "La EPS finalmente autorizo y asigno fecha para la cirugia.",
                "case_story": "La barrera inicial ya fue superada porque la EPS programo el procedimiento.",
                "concrete_request": "Verificar si aun corresponde alguna accion o si el caso quedo resuelto.",
            },
            dates="2026-03-01, 2026-03-18",
        ),
        prior_actions=["eps_pqrs"],
        expected_workflow="derecho_peticion",
        expected_action="Derecho de peticion a EPS",
        expected_preview_status="ok",
    ),
    HealthRegressionCase(
        name="tutela_previa_temeridad",
        description=(
            "Ya presente una tutela por este mismo medicamento y fue negada hace dos semanas. "
            "Quiero volver a presentarla igual porque la EPS sigue sin entregarlo."
        ),
        facts=_base_facts(
            {
                "target_entity": "Capital Salud EPS",
                "eps_name": "Capital Salud EPS",
                "acting_capacity": "nombre_propio",
                "diagnosis": "Epilepsia refractaria",
                "treatment_needed": "Entrega continua de anticonvulsivante formulado por neurologia",
                "urgency_detail": "Sigo en riesgo de convulsiones si no entregan el medicamento.",
                "ongoing_harm": "La falta del medicamento mantiene riesgo actual de crisis convulsivas.",
                "medical_order_date": "2026-03-04",
                "treating_doctor_name": "Dra. Sara Molina",
                "evidence_summary": "Formula medica, historia clinica y fallo anterior.",
                "prior_claim": "si",
                "prior_claim_result": "La EPS sigue sin entregar el medicamento pese a nuevas solicitudes.",
                "prior_tutela": "si",
                "prior_tutela_reason": "Ya hubo una tutela anterior por los mismos hechos y el mismo medicamento.",
                "tutela_previous_action_detail": "Se presento tutela previa y fue negada hace dos semanas.",
                "tutela_other_means_detail": "Se ha insistido ante la EPS, pero el medicamento sigue sin entrega.",
                "tutela_immediacy_detail": "El riesgo actual persiste por falta continua del medicamento.",
                "case_story": "Existe antecedente de tutela previa por el mismo problema medico.",
                "concrete_request": "Evaluar si procede una nueva tutela o si existe riesgo de temeridad.",
            },
            dates="2026-03-04, 2026-03-10",
        ),
        prior_actions=["eps_pqrs"],
        expected_workflow="tutela",
        expected_action="Accion de tutela",
        expected_preview_status="ok",
        expect_tutela_procedencia="media",
    ),
    HealthRegressionCase(
        name="caso_debil_o_incompleto",
        description=(
            "Tengo un problema de salud y quiero demandar porque no me siento bien atendido."
        ),
        facts=_base_facts(
            {
                "acting_capacity": "nombre_propio",
                "case_story": "No explico claramente la EPS, el diagnostico ni el servicio requerido.",
            },
            dates="",
        ),
        prior_actions=[],
        expected_workflow="derecho_peticion",
        expected_action="Derecho de peticion a EPS",
        expected_preview_status="requires_more_data",
    ),
]


def run_case(case: HealthRegressionCase) -> list[str]:
    issues: list[str] = []
    legal_analysis = {
        "recommended_action": "",
        "derechos_vulnerados": ["Derecho fundamental a la salud"],
        "normas_relevantes": ["Constitucion Politica Articulo 86", "Ley 1751 de 2015"],
    }
    workflow = infer_workflow(
        category="Salud",
        description=case.description,
        facts=case.facts,
        legal_analysis=legal_analysis,
        prior_actions=case.prior_actions,
    )
    if workflow["workflow_type"] != case.expected_workflow:
        issues.append(f"workflow esperado={case.expected_workflow} obtenido={workflow['workflow_type']}")
    if workflow["recommended_action"] != case.expected_action:
        issues.append(f"accion esperada={case.expected_action} obtenida={workflow['recommended_action']}")

    preview_gate = validate_submission_readiness(
        category="Salud",
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=case.description,
        facts=case.facts,
        prior_actions=case.prior_actions,
        stage="preview",
    )
    if preview_gate["status"] != case.expected_preview_status:
        issues.append(f"preview esperado={case.expected_preview_status} obtenido={preview_gate['status']}")

    agent_state = build_health_agent_state(
        category="Salud",
        workflow_type=workflow["workflow_type"],
        recommended_action=workflow["recommended_action"],
        description=case.description,
        facts=case.facts,
    )
    if bool(agent_state.get("enabled")) != case.expect_agent_enabled:
        issues.append("agent_state no coincide con lo esperado")

    if workflow["workflow_type"] == "tutela" and case.expect_tutela_procedencia:
        procedencia = evaluate_tutela_procedencia(
            description=case.description,
            facts=case.facts,
            prior_actions=case.prior_actions,
        )
        if procedencia["procedencia"] != case.expect_tutela_procedencia:
            issues.append(
                f"procedencia esperada={case.expect_tutela_procedencia} obtenida={procedencia['procedencia']}"
            )
    return issues


def main() -> int:
    failures: list[tuple[str, list[str]]] = []
    for case in CASES:
        issues = run_case(case)
        if issues:
            failures.append((case.name, issues))
            print(f"[FAIL] {case.name}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"[OK]   {case.name}")

    if failures:
        print("")
        print(f"Resultado: {len(failures)} caso(s) con hallazgos.")
        return 1

    print("")
    print(f"Resultado: {len(CASES)} caso(s) validados correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
