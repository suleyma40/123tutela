from __future__ import annotations

from typing import Any

from backend.legal_sources import validate_document_citations


OFFICIAL_SOURCES = [
    {
        "level": 1,
        "label": "Fuentes primarias para jurisprudencia",
        "sources": [
            "www.corteconstitucional.gov.co/relatoria/",
            "www.consejodeestado.gov.co",
        ],
    },
    {
        "level": 2,
        "label": "Fuentes secundarias para contraste jurisprudencial",
        "sources": [
            "www.vlex.com.co",
        ],
    },
    {
        "level": 3,
        "label": "Fuentes primarias para normas y regulacion",
        "sources": [
            "SUIN-Juriscol",
            "secretariasenado.gov.co",
            "Ministerios y superintendencias competentes segun el caso",
            "Leyes, decretos y resoluciones vigentes",
        ],
    },
    {
        "level": 4,
        "label": "Fuentes no aptas para sustento principal",
        "sources": [
            "Blogs",
            "Foros",
            "Resenas sin fuente oficial",
            "Redes sociales",
            "PDFs no verificables",
        ],
    },
]


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value in (None, ""):
        return []
    return [value]


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def build_source_validation_policy() -> dict[str, Any]:
    return {
        "hierarchy": OFFICIAL_SOURCES,
        "required_fields_for_use": [
            "tipo_fuente",
            "corporacion",
            "numero_sentencia_o_norma",
            "fecha",
            "url_verificada",
            "extracto_relevante",
            "tema_juridico",
            "nivel_confiabilidad",
        ],
        "usage_rule": (
            "Solo se puede usar una norma o sentencia como sustento principal si la referencia es verificable, "
            "coinciden numero, ano y autoridad, y el extracto si responde al punto juridico del caso."
        ),
        "anti_fabrication_rule": (
            "Si no hay soporte verificable, no inventar citas ni inferir jurisprudencia. "
            "El sistema debe advertir que no se encontro soporte suficientemente verificable."
        ),
        "verified_sources": [],
        "research_status": "not_started",
    }


def _build_question(
    *,
    question_id: str,
    prompt: str,
    reason: str,
    priority: str = "media",
    field: str | None = None,
    route: str | None = None,
) -> dict[str, Any]:
    return {
        "id": question_id,
        "question": prompt,
        "reason": reason,
        "priority": priority,
        "field": field,
        "route": route,
        "responded": False,
    }


def _is_ai_owned_quality_issue(issue: object) -> bool:
    text = _lower(issue)
    if not text:
        return False
    markers = [
        "jurisprudencia sin soporte oficial",
        "soporte jurisprudencial",
        "fuentes verificadas",
        "fuente verificada",
        "sustento juridico",
        "depurar internamente",
        "reforzar internamente",
        "precedente no verificado",
        "verificable",
    ]
    return any(marker in text for marker in markers)


def _field_has_value(case: dict[str, Any], field: str | None) -> bool:
    if not field:
        return False
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    if _text(intake.get(field)) or _text(facts.get(field)):
        return True
    if field == "target_entity":
        return bool(_text((case.get("routing") or {}).get("primary_target", {}).get("name")))
    return False


def _get_actionable_high_priority_questions(case: dict[str, Any]) -> list[dict[str, Any]]:
    facts = case.get("facts") or {}
    pending_questions = facts.get("pending_questions") or []
    actionable: list[dict[str, Any]] = []
    for item in pending_questions:
        if item.get("priority") != "alta":
            continue
        if _field_has_value(case, item.get("field")):
            continue
        actionable.append(item)
    return actionable


def _field_location_label(field: str | None, recommended_action: str = "") -> str:
    normalized = _lower(field)
    action = _lower(recommended_action)

    if normalized in {
        "full_name",
        "document_number",
        "address",
        "phone",
        "copy_email",
    }:
        return "Datos personales y de contacto"
    if normalized in {
        "target_entity",
        "target_pqrs_email",
        "target_phone",
        "target_website",
        "target_identifier",
    }:
        return "Entidad y canal de radicacion"
    if normalized in {
        "key_dates",
        "bank_event_date",
        "prior_claim_date",
        "petition_previous_submission_date",
        "tutela_ruling_date",
    }:
        return "Fechas importantes del caso"
    if normalized in {
        "case_story",
        "concrete_request",
        "numbered_requests",
        "request_type",
        "requested_data_action",
        "administrative_requested_fix",
    }:
        return "Solucion concreta que necesitas"
    if normalized in {
        "available_evidence",
        "evidence_summary",
        "supporting_documents",
    }:
        return "Pruebas y anexos"
    if normalized.startswith("bank_") or normalized in {
        "disputed_charge",
        "refund_destination",
    }:
        return "Detalle del caso financiero"
    if normalized in {
        "diagnosis",
        "treatment_needed",
        "urgency_detail",
        "eps_name",
    }:
        return "Detalle del caso de salud"
    if normalized in {
        "disputed_data",
        "requested_data_action",
    }:
        return "Detalle del dato o reporte cuestionado"
    if normalized.startswith("tutela_") or normalized in {
        "acting_capacity",
        "represented_person_name",
        "represented_person_age",
        "represented_person_document",
        "special_protection",
        "prior_tutela",
        "prior_tutela_reason",
        "ongoing_harm",
        "subsidiarity_support",
    }:
        return "Preguntas finas para tutela"
    if "tutela" in action:
        return "Paso de tutela y urgencia actual"
    if "peticion" in action:
        return "Paso de derecho de peticion"
    return "Completa datos del caso"


def _build_actionable_gap(
    *,
    field: str | None,
    label: str,
    prompt: str,
    recommended_action: str = "",
    priority: str = "alta",
) -> dict[str, Any]:
    return {
        "field": field,
        "label": label,
        "prompt": prompt,
        "where_to_fix": _field_location_label(field, recommended_action),
        "priority": priority,
    }


def evaluate_tutela_procedencia(
    *,
    description: str,
    facts: dict[str, Any],
    prior_actions: list[str],
) -> dict[str, Any]:
    text = _lower(description)
    intake = facts.get("intake_form") or {}
    entities = [str(item).strip() for item in _list(facts.get("entidades_involucradas")) if _text(item)]
    dates = _text(facts.get("fechas_mencionadas"))
    case_story = _text(facts.get("hechos_principales")) or text
    special_protection = _lower(intake.get("special_protection"))
    prior_tutela = _lower(intake.get("prior_tutela") or intake.get("prior_tutela_reason"))
    prior_claim = _lower(intake.get("prior_claim") or intake.get("prior_claim_result"))

    causales: list[str] = []
    faltantes: list[str] = []
    warnings: list[str] = []

    legitimacion_activa = "alta"
    if not _has_any(text, ["yo", "mi", "mio", "madre", "hijo", "acudiente", "agente oficioso", "representante"]):
        legitimacion_activa = "media"
        faltantes.append("Aclarar quien presenta la tutela y en calidad de que lo hace.")

    legitimacion_pasiva = "alta" if entities else "baja"
    if legitimacion_pasiva == "baja":
        causales.append("Legitimacion por pasiva no clara")
        faltantes.append("Identificar con claridad la autoridad o particular accionado.")

    inmediatez = "alta"
    if not dates:
        inmediatez = "media"
        faltantes.append("Precisar fechas de los hechos o explicar si la vulneracion sigue ocurriendo.")
    elif _has_any(_lower(dates), ["ano pasado", "2023", "2024"]) and not _has_any(text, ["continua", "sigue", "actualmente"]):
        inmediatez = "baja"
        causales.append("Riesgo de inmediatez")

    subsidiariedad = "alta" if prior_actions or prior_claim in {"si", "sí", "reclame", "reclamo", "radicado"} else "media"
    if subsidiariedad != "alta" and not _has_any(text, ["urgencia", "grave", "riesgo", "perjuicio irremediable", "menor", "embarazada", "discapacidad"]):
        causales.append("Subsidiariedad incompleta")
        faltantes.append("Explicar gestion previa o por que la tutela es urgente pese a no haber otra via agotada.")

    perjuicio_irremediable = "alta" if _has_any(text, ["urgencia", "grave", "riesgo", "perjuicio irremediable", "vida", "salud", "minimo vital"]) else "media"
    if perjuicio_irremediable != "alta":
        warnings.append("Conviene explicar mejor que dano sigue ocurriendo hoy o por que el caso sigue siendo urgente.")

    hecho_superado = _has_any(text, ["ya resolvieron", "ya entregaron", "ya respondieron", "solucionado"])
    if hecho_superado:
        causales.append("Posible hecho superado o carencia actual de objeto")

    temeridad = "media" if _has_any(prior_tutela, ["si", "sí"]) else "baja"
    if temeridad == "media":
        causales.append("Revisar posible temeridad")
        faltantes.append("Aclarar si ya existe otra tutela por los mismos hechos, derechos y pretensiones.")

    prueba_minima = "alta" if _has_any(text, ["anexo", "soporte", "formula", "orden", "correo", "chat", "captura", "radicado", "factura"]) else "media"
    if prueba_minima != "alta":
        faltantes.append("Describir al menos un soporte minimo disponible o el motivo por el cual no se tiene.")

    score = 0
    score += 2 if legitimacion_pasiva == "alta" else 0
    score += 2 if inmediatez == "alta" else 1 if inmediatez == "media" else 0
    score += 2 if subsidiariedad == "alta" else 1 if subsidiariedad == "media" else 0
    score += 2 if perjuicio_irremediable == "alta" else 1
    score += 1 if prueba_minima == "alta" else 0
    if temeridad == "media":
        score -= 2
    if hecho_superado:
        score -= 2

    if score >= 7 and not causales:
        procedencia = "alta"
        riesgo = "bajo"
        recomendacion = "redactar"
    elif score >= 4:
        procedencia = "media"
        riesgo = "medio"
        recomendacion = "pedir_mas_datos"
    else:
        procedencia = "baja"
        riesgo = "alto"
        recomendacion = "escalar"

    if special_protection and special_protection not in {"no aplica", "ninguno"}:
        warnings.append("Hay sujeto de especial proteccion; conviene dejarlo claro porque refuerza la urgencia del caso.")

    return {
        "procedencia": procedencia,
        "riesgo_improcedencia": riesgo,
        "causales_detectadas": list(dict.fromkeys(causales)),
        "faltantes_criticos": list(dict.fromkeys(faltantes)),
        "recomendacion": recomendacion,
        "subscores": {
            "legitimacion_activa": legitimacion_activa,
            "legitimacion_pasiva": legitimacion_pasiva,
            "inmediatez": inmediatez,
            "subsidiariedad": subsidiariedad,
            "perjuicio_irremediable": perjuicio_irremediable,
            "temeridad": temeridad,
            "prueba_minima": prueba_minima,
            "hecho_superado": hecho_superado,
        },
        "warnings": list(dict.fromkeys(warnings)),
    }


def collect_pending_questions(
    *,
    category: str,
    workflow_type: str,
    description: str,
    facts: dict[str, Any],
    prior_actions: list[str],
) -> list[dict[str, Any]]:
    intake = facts.get("intake_form") or {}
    text = _lower(
        " ".join(
            str(part).strip()
            for part in [
                description,
                facts.get("hechos_principales"),
                intake.get("case_story"),
                intake.get("concrete_request"),
                intake.get("prior_claim_result"),
                intake.get("refund_destination"),
                intake.get("bank_claim_goal"),
            ]
            if _text(part)
        )
    )
    questions: list[dict[str, Any]] = []
    category_lower = _lower(category)
    prior_claim_value = _lower(intake.get("prior_claim"))
    prior_claim_yes = prior_claim_value in {"si", "sí", "reclame", "reclamo"}
    prior_claim_no = prior_claim_value in {"no", "aun no", "aún no", "no_aun_no"}

    if not _text(facts.get("fechas_mencionadas")):
        questions.append(
            _build_question(
                question_id="fecha_hechos",
                prompt="Cual es la fecha exacta o aproximada de los hechos principales?",
                reason="La cronologia todavia no es suficientemente clara.",
                priority="alta",
                field="key_dates",
                route="B",
            )
        )
    if not _text(intake.get("concrete_request")) and not _has_any(text, ["solicito", "pido", "ordenen", "requiero"]):
        questions.append(
            _build_question(
                question_id="pretension_concreta",
                prompt="Que necesitas que pase para solucionar tu problema: devolver dinero, entregar un medicamento, corregir un dato, responder un reclamo u otra medida concreta?",
                reason="Hace falta entender el resultado practico que esperas obtener.",
                priority="alta",
                field="concrete_request",
                route="B",
            )
        )
    if not _text(intake.get("copy_email")):
        questions.append(
            _build_question(
                question_id="canal_respuesta",
                prompt="A que correo o direccion quieres recibir respuesta formal?",
                reason="Hace falta definir el canal de notificacion.",
                priority="media",
                field="copy_email",
                route="A",
            )
        )
    if not _has_any(text, ["prueba", "adjunto", "chat", "captura", "correo", "pdf", "pantallazo", "radicado", "formula", "extracto"]):
        questions.append(
            _build_question(
                question_id="soportes_disponibles",
                prompt="Que soportes tienes disponibles: chat, fotos, PDF, radicado, extracto, formula o correo?",
                reason="No se describen soportes minimos del caso.",
                priority="media",
                field="available_evidence",
                route="B",
            )
        )

    if category_lower == "bancos":
        if not _text(intake.get("bank_amount_involved")) and not _has_any(text, ["monto", "valor", "$", "pesos"]):
            questions.append(
                _build_question(
                    question_id="valor_cobro",
                    prompt="De cuanto es el cobro cuestionado o cuanto te han cobrado en total?",
                    reason="Falta cuantificar el perjuicio economico.",
                    priority="alta",
                    field="bank_amount_involved",
                    route="B",
                )
            )
        if not _text(intake.get("bank_product_type")):
            questions.append(
                _build_question(
                    question_id="producto_bancario",
                    prompt="Que producto financiero esta afectado: tarjeta, cuenta, credito o seguro asociado?",
                    reason="No esta completamente identificado el producto involucrado.",
                    priority="alta",
                    field="bank_product_type",
                    route="B",
                )
            )
        if not _text(intake.get("bank_event_date")):
            questions.append(
                _build_question(
                    question_id="fecha_primer_cobro",
                    prompt="Desde que fecha viste el primer cobro, reporte o bloqueo bancario?",
                    reason="La cronologia financiera necesita un hito temporal claro.",
                    priority="alta",
                    field="bank_event_date",
                    route="B",
                )
            )
        if not _text(intake.get("bank_account_reference")) and not _has_any(text, ["tarjeta terminada", "cuenta", "producto", "ultimos 4", "referencia"]):
            questions.append(
                _build_question(
                    question_id="referencia_producto",
                    prompt="Tienes numero de cuenta, ultimos 4 digitos de la tarjeta o referencia del producto?",
                    reason="Hace falta un identificador del producto financiero.",
                    priority="media",
                    field="bank_account_reference",
                    route="B",
                )
            )
        if not _text(intake.get("prior_claim_date")) and prior_claim_yes:
            questions.append(
                _build_question(
                    question_id="fecha_reclamo_previo_banco",
                    prompt="En que fecha reclamaste al banco y por cual canal presentaste la reclamacion?",
                    reason="Hace falta trazabilidad del reclamo previo.",
                    priority="alta",
                    field="prior_claim_date",
                    route="B",
                )
            )
        if prior_claim_yes and not _text(intake.get("prior_claim_result")):
            questions.append(
                _build_question(
                    question_id="reclamo_previo_banco",
                    prompt="Cuando reclamaste al banco, por que canal y que te respondieron?",
                    reason="La reclamacion previa es critica para este tipo de caso.",
                    priority="alta",
                    field="prior_claim_result",
                    route="B",
                )
            )
        if not _text(intake.get("refund_destination")) and not _has_any(
            text,
            ["devolver a", "consignar", "cuenta de devolucion", "reintegrar", "misma tarjeta", "misma cuenta", "mismo producto", "a la misma tarjeta", "a la misma cuenta", "a mi tarjeta", "a mi cuenta", "a la tarjeta"],
        ):
            questions.append(
                _build_question(
                    question_id="cuenta_reintegro",
                    prompt="Si pides devolucion del dinero, a que cuenta o producto debe hacerse el reintegro?",
                    reason="La solicitud economica necesita un destino claro de pago o reverso.",
                    priority="media",
                    field="refund_destination",
                    route="A",
                )
            )

    if category_lower == "salud":
        if not _text(intake.get("target_entity")) and not _text(intake.get("eps_name")) and not _has_any(text, ["eps", "ips"]):
            questions.append(
                _build_question(
                    question_id="eps",
                    prompt="Cual EPS o IPS esta vulnerando tu derecho?",
                    reason="Falta identificar la entidad accionada en salud.",
                    priority="alta",
                    field="target_entity",
                    route="B",
                )
            )
        if not _text(intake.get("diagnosis")) and not _has_any(text, ["diagnostico", "diagnóstico", "enfermedad", "condicion", "condición"]):
            questions.append(
                _build_question(
                    question_id="diagnostico",
                    prompt="Cual es el diagnostico o condicion medica principal?",
                    reason="Hace falta el cuadro clinico que explica la urgencia del caso.",
                    priority="alta",
                    field="diagnosis",
                    route="B",
                )
            )
        if not _text(intake.get("treatment_needed")) and not _has_any(text, ["formula", "orden medica", "orden médica", "medicamento", "tratamiento", "procedimiento"]):
            questions.append(
                _build_question(
                    question_id="servicio_ordenado",
                    prompt="Que medicamento, procedimiento o tratamiento te ordenaron exactamente?",
                    reason="La orden medica o el servicio requerido todavia no es claro.",
                    priority="alta",
                    field="treatment_needed",
                    route="B",
                )
            )
        if not _text(intake.get("urgency_detail")) and not _has_any(text, ["urgencia", "riesgo", "dolor", "agrav", "suspender", "empeora", "vida"]):
            questions.append(
                _build_question(
                    question_id="urgencia_salud",
                    prompt="Por que este caso de salud es urgente hoy: dolor, agravacion, suspension del tratamiento o riesgo vital?",
                    reason="La tutela en salud necesita una urgencia mejor documentada.",
                    priority="alta",
                    field="urgency_detail",
                    route="B",
                )
            )
        if not _text(intake.get("prior_claim_result")) and not _has_any(text, ["radicado", "autorizacion", "autorización", "negaron", "no entregaron", "demoraron"]):
            questions.append(
                _build_question(
                    question_id="respuesta_eps",
                    prompt="Que respondio la EPS o que barrera concreta impuso: negativa, demora, falta de agenda o no entrega?",
                    reason="Hace falta describir la respuesta o barrera administrativa de la entidad de salud.",
                    priority="media",
                    field="prior_claim_result",
                    route="B",
                )
            )

    if category_lower == "datos":
        if not _text(intake.get("disputed_data")) and not _has_any(text, ["dato", "reporte", "historial", "datacredito", "cifin"]):
            questions.append(
                _build_question(
                    question_id="dato_cuestionado",
                    prompt="Que dato, reporte o registro personal estas cuestionando exactamente?",
                    reason="No esta claro cual es el dato o reporte discutido.",
                    priority="alta",
                    field="disputed_data",
                    route="B",
                )
            )
        if not _text(intake.get("requested_data_action")):
            questions.append(
                _build_question(
                    question_id="accion_sobre_dato",
                    prompt="Que esta mal con ese dato o reporte y como deberia quedar corregido: actualizado, eliminado, corregido o con prueba de autorizacion?",
                    reason="Hace falta entender el error concreto del dato y el ajuste esperado.",
                    priority="alta",
                    field="requested_data_action",
                    route="B",
                )
            )
        if not _text(intake.get("prior_claim_result")) and not prior_actions:
            questions.append(
                _build_question(
                    question_id="reclamo_previo_datos",
                    prompt="Ya reclamaste ante la fuente o central de riesgo? Si si, indica fecha, canal y respuesta.",
                    reason="La via previa es importante en habeas data salvo urgencia grave.",
                    priority="alta",
                    field="prior_claim_result",
                    route="B",
                )
            )

    if workflow_type == "derecho_peticion":
        if not _text(intake.get("request_type")):
            questions.append(
                _build_question(
                    question_id="tipo_peticion",
                    prompt="Que necesitas de la entidad en este momento: informacion, copias de documentos, una respuesta sobre tu caso o que corrijan una actuacion?",
                    reason="Debemos entender el objetivo practico de la peticion.",
                    priority="media",
                    field="request_type",
                    route="A",
                )
            )
        if not _text(intake.get("numbered_requests")):
            questions.append(
                _build_question(
                    question_id="solicitudes_numeradas",
                    prompt="Si la entidad te respondiera hoy, cuales serian las 2 o 3 respuestas o soluciones concretas que necesitas recibir?",
                    reason="Hace falta identificar las respuestas concretas que la entidad debe dar.",
                    priority="alta",
                    field="numbered_requests",
                    route="B",
                )
            )

    if workflow_type == "tutela":
        procedencia = evaluate_tutela_procedencia(description=description, facts=facts, prior_actions=prior_actions)
        if _lower(category) == "salud":
            if not _text(intake.get("medical_order_date")):
                questions.append(
                    _build_question(
                        question_id="orden_medica_fecha",
                        prompt="En que fecha te ordenaron el examen, medicamento o procedimiento que hoy estas reclamando?",
                        reason="Hace falta la fecha de la orden medica para sostener la cronologia de la tutela.",
                        priority="alta",
                        field="medical_order_date",
                        route="B",
                    )
                )
            if not _text(intake.get("treating_doctor_name")):
                questions.append(
                    _build_question(
                        question_id="medico_tratante",
                        prompt="Como se llama el medico tratante que ordeno el servicio y, si lo recuerdas, en que IPS te atendieron?",
                        reason="Necesitamos identificar quien ordeno el servicio y desde donde se emitio la orden medica.",
                        priority="alta",
                        field="treating_doctor_name",
                        route="B",
                    )
                )
            if not _text(intake.get("eps_request_date")):
                questions.append(
                    _build_question(
                        question_id="solicitud_eps_fecha",
                        prompt="En que fecha pediste a la EPS la autorizacion del examen, medicamento o procedimiento?",
                        reason="Hace falta la fecha de la solicitud previa ante la EPS.",
                        priority="alta",
                        field="eps_request_date",
                        route="B",
                    )
                )
            if not _text(intake.get("eps_response_detail")):
                questions.append(
                    _build_question(
                        question_id="respuesta_eps_detalle",
                        prompt="Que hizo la EPS despues: nego, guardo silencio, demoro, no agendo o puso otra barrera concreta?",
                        reason="Necesitamos saber la respuesta o barrera real de la EPS para sustentar la vulneracion.",
                        priority="alta",
                        field="eps_response_detail",
                        route="B",
                    )
                )
        if procedencia["subscores"]["subsidiariedad"] != "alta":
            questions.append(
                _build_question(
                    question_id="subsidiariedad",
                    prompt="Antes de llegar hasta aqui, que hiciste para resolver el problema y que paso despues: te respondieron, no te contestaron o el dano sigue igual?",
                    reason="Hace falta la secuencia real de gestiones previas y el estado actual del problema.",
                    priority="alta",
                    field="subsidiarity_support",
                    route="B",
                )
            )
        if procedencia["subscores"]["temeridad"] == "media":
            questions.append(
                _build_question(
                    question_id="temeridad",
                    prompt="Ya habias presentado antes una tutela, peticion o reclamo por este mismo problema? Si si, cuenta que presentaste y que te respondieron.",
                    reason="Necesitamos saber si ya hubo actuaciones previas sobre los mismos hechos.",
                    priority="alta",
                    field="prior_tutela_reason",
                    route="B",
                )
            )
        if procedencia["subscores"]["inmediatez"] != "alta":
            questions.append(
                _build_question(
                    question_id="inmediatez",
                    prompt="Que esta pasando hoy que hace urgente este caso: el dano sigue, empeoro, te siguen cobrando, no entregan el servicio o el riesgo continua?",
                    reason="Hace falta describir el dano actual o la urgencia presente.",
                    priority="alta",
                    field="ongoing_harm",
                    route="B",
                )
            )

    deduped: dict[str, dict[str, Any]] = {}
    for item in questions:
        deduped[item["id"]] = item
    return list(deduped.values())


def classify_case_route(
    *,
    workflow_type: str,
    facts: dict[str, Any],
    routing: dict[str, Any],
    intake_review: dict[str, Any],
    preview_gate: dict[str, Any],
    document_rule_review: dict[str, Any],
    tutela_procedencia: dict[str, Any] | None,
    pending_questions: list[dict[str, Any]],
) -> str:
    blocking = (
        len(intake_review.get("blocking_issues", []))
        + len(preview_gate.get("blocking_issues", []))
        + len(document_rule_review.get("blocking_issues", []))
    )
    entities = [
        _text(item)
        for item in _list(facts.get("entidades_involucradas"))
        if _text(item) and "representante" not in _lower(item)
    ]
    multiple_entities = len(entities) > 1
    low_procedencia = tutela_procedencia and tutela_procedencia.get("procedencia") == "baja"
    high_risk = tutela_procedencia and tutela_procedencia.get("riesgo_improcedencia") == "alto"
    no_target = not (routing.get("primary_target") or {}).get("name")

    if low_procedencia or high_risk or multiple_entities:
        return "C"
    if blocking or pending_questions or no_target:
        return "B"
    return "A"


def build_dx_result(
    *,
    workflow_type: str,
    recommended_action: str,
    facts: dict[str, Any],
    routing: dict[str, Any],
    intake_review: dict[str, Any],
    preview_gate: dict[str, Any],
    document_rule_review: dict[str, Any],
    tutela_procedencia: dict[str, Any] | None,
    pending_questions: list[dict[str, Any]],
) -> dict[str, Any]:
    blocking = list(
        dict.fromkeys(
            intake_review.get("blocking_issues", [])
            + preview_gate.get("blocking_issues", [])
            + document_rule_review.get("blocking_issues", [])
            + (tutela_procedencia.get("faltantes_criticos", []) if tutela_procedencia else [])
        )
    )
    warnings = list(
        dict.fromkeys(
            intake_review.get("warnings", [])
            + preview_gate.get("warnings", [])
            + document_rule_review.get("warnings", [])
            + (tutela_procedencia.get("warnings", []) if tutela_procedencia else [])
        )
    )
    urgent = workflow_type == "tutela" or bool(tutela_procedencia and tutela_procedencia.get("subscores", {}).get("perjuicio_irremediable") == "alta")

    if tutela_procedencia and tutela_procedencia.get("procedencia") == "baja":
        viability = "baja"
        color = "rojo"
    elif blocking:
        viability = "media"
        color = "amarillo"
    elif warnings:
        viability = "media"
        color = "naranja"
    else:
        viability = "alta"
        color = "verde"

    route = classify_case_route(
        workflow_type=workflow_type,
        facts=facts,
        routing=routing,
        intake_review=intake_review,
        preview_gate=preview_gate,
        document_rule_review=document_rule_review,
        tutela_procedencia=tutela_procedencia,
        pending_questions=pending_questions,
    )
    if route == "C" and color != "rojo":
        color = "naranja"

    requires_human_review = route == "C"
    automatable = route == "A"
    if route == "A":
        next_step = "Caso viable y automatizable. Puede pasar a redaccion cuando complete pago o revision final."
    elif route == "B":
        next_step = "Faltan datos o soportes clave. El sistema debe hacer preguntas adicionales antes de redactar."
    else:
        next_step = "Caso viable con riesgo o complejidad alta. Conviene revision humana o investigacion juridica reforzada."

    return {
        "viability_preliminary": viability,
        "traffic_light": color,
        "route": route,
        "recommended_document": recommended_action,
        "urgency_level": "alto" if urgent else "medio" if warnings else "bajo",
        "requires_human_review": requires_human_review,
        "automatable": automatable,
        "blocking_reasons": blocking,
        "warnings": warnings,
        "missing_questions": [item["id"] for item in pending_questions],
        "next_step": next_step,
    }


def build_layer_outputs(
    *,
    dx_result: dict[str, Any],
    workflow_type: str,
    recommended_action: str,
    pending_questions: list[dict[str, Any]],
    tutela_procedencia: dict[str, Any] | None,
    final_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route = dx_result.get("route")
    stage = "caso_viable" if dx_result.get("viability_preliminary") == "alta" else "informacion_incompleta"
    if dx_result.get("traffic_light") == "rojo":
        stage = "caso_no_viable"
    elif route == "C":
        stage = "escalar_revision_humana"
    elif pending_questions:
        stage = "preguntas_adicionales_requeridas"

    layers = {
        "current_stage": stage,
        "dx": {
            "status": "completed",
            "result": dx_result,
        },
        "analysis": {
            "status": "completed",
            "workflow_type": workflow_type,
            "recommended_action": recommended_action,
            "tutela_procedencia": tutela_procedencia or {},
        },
        "research": {
            "status": "pending" if route != "C" else "recommended",
            "verified_sources_count": 0,
        },
        "questions": {
            "status": "pending" if pending_questions else "not_required",
            "count": len(pending_questions),
        },
        "draft": {
            "status": "ready" if route == "A" else "blocked",
        },
        "delivery_validation": final_validation or {
            "status": "pending",
            "apto_para_entrega": False,
        },
    }
    return layers


def build_final_validation(
    *,
    case: dict[str, Any],
    document: str,
    quality_review: dict[str, Any],
) -> dict[str, Any]:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    legal_analysis = case.get("legal_analysis") or {}
    recommended_action = _lower(case.get("recommended_action"))
    lowered = _lower(document)
    blocking_issues: list[str] = []
    warnings: list[str] = []
    actionable_gaps: list[dict[str, Any]] = []
    high_priority_questions = _get_actionable_high_priority_questions(case)
    route = ((case.get("routing") or {}).get("case_route") or (facts.get("dx_result") or {}).get("route") or "").strip()

    if not _text(case.get("recommended_action")):
        blocking_issues.append("No esta claramente definido el tipo de accion o documento.")

    if not _text((case.get("routing") or {}).get("primary_target", {}).get("name")) and not _list(facts.get("entidades_involucradas")):
        blocking_issues.append("La entidad accionada o destinataria no quedo suficientemente clara.")

    if not _text(facts.get("pretension_concreta")) and not _has_any(lowered, ["solicito", "pretension", "solicitudes"]):
        blocking_issues.append("Las pretensiones no corresponden claramente al caso o siguen siendo vagas.")
    if route == "C":
        blocking_issues.append("El expediente aun no esta en ruta automatizable. Debe completar preguntas o pasar revision previa antes de entregar.")
    if high_priority_questions:
        blocking_issues.append("Faltan datos criticos del caso antes de entregar el documento final.")
        for question in high_priority_questions:
            actionable_gaps.append(
                _build_actionable_gap(
                    field=question.get("field"),
                    label=question.get("reason") or question.get("question") or "Dato critico faltante",
                    prompt=question.get("question") or question.get("reason") or "Completa este dato antes de entregar.",
                    recommended_action=recommended_action,
                    priority=question.get("priority") or "alta",
                )
            )

    if not _text(facts.get("fechas_mencionadas")):
        warnings.append("La cronologia sigue debil porque faltan fechas o periodos claros.")

    source_policy = facts.get("source_validation_policy") or {}
    citation_guard = validate_document_citations(document=document, source_validation_policy=source_policy)
    if not _list(source_policy.get("verified_sources")) and _has_any(recommended_action, ["tutela", "impugnacion", "desacato", "cumplimiento"]):
        warnings.append("No hay fuentes verificadas cargadas todavia; el sustento jurisprudencial debe mantenerse conservador.")
    if source_policy.get("unresolved_precedents"):
        warnings.append(
            "Existen referencias jurisprudenciales no verificadas automaticamente y fueron excluidas como sustento principal."
        )
    if citation_guard.get("has_unverified_citations"):
        blocking_issues.append(
            "El documento final contiene citas o referencias juridicas no verificadas por el registro interno."
        )
        warnings.append(
            "Referencias pendientes de verificacion detectadas: "
            + ", ".join((citation_guard.get("unresolved_detected_references") or [])[:4])
            + "."
        )

    if _has_any(lowered, ["ganaras seguro", "resultado garantizado", "ganara el proceso", "exito asegurado"]):
        blocking_issues.append("El documento promete resultados o contiene afirmaciones impropias.")
    if (
        _has_any(lowered, ["t-", "su-", "c-"])
        and not _list(source_policy.get("verified_precedents"))
        and not _list(citation_guard.get("verified_detected_references"))
    ):
        warnings.append("La IA debe reforzar o depurar internamente el soporte jurisprudencial antes de la entrega final.")

    if "accion de tutela" in recommended_action:
        if _text(intake.get("acting_capacity")) and _lower(intake.get("acting_capacity")) != "nombre_propio":
            if not _text(intake.get("represented_person_name")):
                blocking_issues.append("La tutela debe identificar con claridad a la persona representada o al menor afectado.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="represented_person_name",
                        label="Falta identificar a la persona representada",
                        prompt="Completa el nombre del menor o de la persona por quien actuas.",
                        recommended_action=recommended_action,
                    )
                )
            if not _text(intake.get("represented_person_age")):
                blocking_issues.append("La tutela debe indicar la edad o fecha de nacimiento de la persona representada.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="represented_person_age",
                        label="Falta edad o fecha de nacimiento de la persona representada",
                        prompt="Indica la edad o fecha de nacimiento de la persona representada.",
                        recommended_action=recommended_action,
                    )
                )
        if not _text(intake.get("tutela_other_means_detail")):
            blocking_issues.append("Antes de entregar la tutela debe quedar claro que hiciste antes para resolverlo o por que eso no solucionaba el dano.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="tutela_other_means_detail",
                    label="Falta contar que hiciste antes para resolverlo",
                    prompt="Explica las gestiones previas y que sigue pasando hoy pese a esas gestiones.",
                    recommended_action=recommended_action,
                )
            )
        if not _text(intake.get("tutela_immediacy_detail")):
            blocking_issues.append("Antes de entregar la tutela debe quedar claro que dano o riesgo sigue ocurriendo hoy.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="tutela_immediacy_detail",
                    label="Falta explicar el dano o riesgo actual",
                    prompt="Cuenta que sigue ocurriendo hoy y por que el caso sigue siendo urgente.",
                    recommended_action=recommended_action,
                )
            )
        if not _text(intake.get("tutela_previous_action_detail")):
            blocking_issues.append("Antes de entregar la tutela debe quedar claro si ya hubo otra solicitud o tutela por este mismo problema.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="tutela_previous_action_detail",
                    label="Falta aclarar si ya hubo otra solicitud o tutela",
                    prompt="Indica si ya presentaste otra tutela, peticion o reclamo por estos mismos hechos y que paso.",
                    recommended_action=recommended_action,
                )
            )
        if not _text(intake.get("tutela_oath_statement")) and not _text(intake.get("tutela_no_temperity_detail")):
            blocking_issues.append("Antes de entregar la tutela debe quedar claro si esta es la primera tutela por este problema o que paso con la anterior.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="tutela_oath_statement",
                    label="Falta confirmar si esta es la primera tutela por este problema",
                    prompt="Confirma si esta es la primera tutela o resume que ocurrio con la anterior.",
                    recommended_action=recommended_action,
                )
            )
        if _lower(case.get("categoria")) == "salud":
            if not _text(intake.get("target_entity")):
                blocking_issues.append("En tutela de salud debe quedar claramente identificada la EPS o IPS accionada.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="target_entity",
                        label="Falta identificar la EPS o IPS accionada",
                        prompt="Completa el nombre exacto de la EPS o IPS contra la que va la tutela.",
                        recommended_action=recommended_action,
                    )
                )
            if not _text(intake.get("diagnosis")):
                blocking_issues.append("En tutela de salud falta el diagnostico o condicion medica principal.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="diagnosis",
                        label="Falta el diagnostico o condicion medica principal",
                        prompt="Indica el diagnostico o la condicion medica relevante para el caso.",
                        recommended_action=recommended_action,
                    )
                )
            if not _text(intake.get("treatment_needed")):
                blocking_issues.append("En tutela de salud falta el medicamento, examen o servicio concreto requerido.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="treatment_needed",
                        label="Falta el servicio o tratamiento exacto que necesitas",
                        prompt="Indica el medicamento, procedimiento, examen o servicio ordenado.",
                        recommended_action=recommended_action,
                    )
                )
            has_current_health_facts = any(
                _text(intake.get(field))
                for field in (
                    "urgency_detail",
                    "ongoing_harm",
                    "eps_response_detail",
                    "tutela_immediacy_detail",
                    "tutela_other_means_detail",
                    "tutela_special_protection_detail",
                )
            ) or (
                _text(intake.get("special_protection")) and _lower(intake.get("special_protection")) not in {"no aplica", "ninguno"}
            ) or _has_any(
                text,
                ["riesgo", "dolor", "agrav", "empeor", "crisis", "urgencias", "hospital", "sin medicamento", "sin examen", "sin tratamiento"],
            )
            if not has_current_health_facts:
                blocking_issues.append("En tutela de salud faltan hechos actuales del paciente: que sigue pasando hoy y que riesgo o afectacion continua sin el servicio.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="urgency_detail",
                        label="Falta contar que sigue pasando hoy al paciente",
                        prompt="Describe que sintomas, dolor, suspension del tratamiento, riesgo o empeoramiento siguen ocurriendo hoy.",
                        recommended_action=recommended_action,
                    )
                )
            if not _text(intake.get("medical_order_date")):
                blocking_issues.append("En tutela de salud falta la fecha de la orden medica o de la consulta donde se formulo el servicio.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="medical_order_date",
                        label="Falta la fecha de la orden medica",
                        prompt="Indica la fecha de la cita o de la orden medica donde se solicito el examen, medicamento o procedimiento.",
                        recommended_action=recommended_action,
                    )
                )
            if not _text(intake.get("treating_doctor_name")):
                blocking_issues.append("En tutela de salud falta identificar el medico tratante que ordeno el servicio.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="treating_doctor_name",
                        label="Falta el nombre del medico tratante",
                        prompt="Indica el nombre del medico tratante que ordeno el examen, medicamento o procedimiento.",
                        recommended_action=recommended_action,
                    )
                )
            if not _text(intake.get("eps_request_date")):
                blocking_issues.append("En tutela de salud falta la fecha en que solicitaste la autorizacion ante la EPS.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="eps_request_date",
                        label="Falta la fecha de la solicitud a la EPS",
                        prompt="Indica en que fecha pediste a la EPS la autorizacion o prestacion del servicio.",
                        recommended_action=recommended_action,
                    )
                )
            if not _text(intake.get("eps_response_detail")):
                blocking_issues.append("En tutela de salud falta explicar si la EPS nego, guardo silencio o impuso una barrera concreta.")
                actionable_gaps.append(
                    _build_actionable_gap(
                        field="eps_response_detail",
                        label="Falta la respuesta o barrera concreta de la EPS",
                        prompt="Cuenta si la EPS nego, guardo silencio, demoro, no agendo o impuso otra barrera concreta.",
                        recommended_action=recommended_action,
                    )
                )
    if "derecho de peticion" in recommended_action:
        if not _text(intake.get("numbered_requests")):
            blocking_issues.append("Antes de entregar el derecho de peticion deben quedar claras las 2 o 3 respuestas o soluciones concretas que esperas recibir.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="numbered_requests",
                    label="Faltan las 2 o 3 soluciones concretas que esperas",
                    prompt="Escribe las respuestas o soluciones concretas que necesitas que la entidad entregue.",
                    recommended_action=recommended_action,
                )
            )
        if not _text(intake.get("response_channel")) and not _text(intake.get("copy_email")):
            blocking_issues.append("El derecho de peticion debe indicar un canal de notificacion claro.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="copy_email",
                    label="Falta un canal claro para recibir la respuesta",
                    prompt="Completa el correo o canal donde quieres recibir la respuesta formal.",
                    recommended_action=recommended_action,
                )
            )
        if _lower(intake.get("petition_target_nature")) == "privada" and not _text(intake.get("petition_private_ground")):
            blocking_issues.append("Si la peticion se dirige a un particular, debe explicarse el fundamento juridico para exigir respuesta.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="petition_private_ground",
                    label="Falta explicar por que ese particular debe responder",
                    prompt="Indica por que ese particular esta obligado a responderte en este caso.",
                    recommended_action=recommended_action,
                )
            )
    if "reclamacion financiera" in recommended_action:
        if not _text(intake.get("bank_product_type")):
            blocking_issues.append("La reclamacion financiera debe identificar el producto bancario o financiero afectado.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="bank_product_type",
                    label="Falta identificar el producto financiero afectado",
                    prompt="Indica si el caso es sobre tarjeta, cuenta, credito, seguro u otro producto.",
                    recommended_action=recommended_action,
                )
            )
        if not _text(intake.get("disputed_charge")):
            blocking_issues.append("La reclamacion financiera debe identificar el cobro, seguro o cargo discutido.")
            actionable_gaps.append(
                _build_actionable_gap(
                    field="disputed_charge",
                    label="Falta identificar el cobro o cargo discutido",
                    prompt="Indica cual cobro, seguro o cargo estas cuestionando exactamente.",
                    recommended_action=recommended_action,
                )
            )
        if not _text(intake.get("bank_amount_involved")):
            warnings.append("Conviene precisar el monto discutido para fortalecer la devolucion o reverso solicitado.")
        if _lower(intake.get("prior_claim")) not in {"si", "sÃ­", "reclame", "reclamo"} and not _text(intake.get("prior_claim_result")):
            blocking_issues.append("Antes de entregar una reclamacion financiera debe quedar documentado el reclamo previo o su justificacion.")
    if "habeas data" in recommended_action:
        if not _text(intake.get("disputed_data")):
            blocking_issues.append("En habeas data debe identificarse el dato, reporte o registro cuestionado.")
        if not _text(intake.get("requested_data_action")):
            blocking_issues.append("En habeas data debe quedar clara la accion solicitada sobre el dato.")
        if not _text(intake.get("prior_claim_result")):
            warnings.append("Conviene dejar trazabilidad del reclamo previo a la fuente o central de riesgo.")

    financial_claim_block = "Antes de entregar una reclamacion financiera debe quedar documentado el reclamo previo o su justificacion."
    if "reclamacion financiera" in recommended_action:
        prior_claim = _lower(intake.get("prior_claim"))
        if prior_claim in {"no", "aun no", "aún no", "no_aun_no"} and financial_claim_block in blocking_issues:
            blocking_issues = [issue for issue in blocking_issues if issue != financial_claim_block]
            warnings.append(
                "La IA tratara este escrito como reclamacion financiera directa inicial y dejara constancia de que aun no existe respuesta previa del banco."
            )

    if quality_review.get("blocking_issues"):
        blocking_issues.extend(
            issue for issue in quality_review["blocking_issues"] if not _is_ai_owned_quality_issue(issue)
        )
        if any(_is_ai_owned_quality_issue(issue) for issue in quality_review["blocking_issues"]):
            warnings.append("La IA seguira depurando internamente fuentes y jurisprudencia verificable antes de la entrega final.")

    fallback_gap_rules = [
        (
            "Antes de entregar una reclamacion financiera debe quedar documentado el reclamo previo o su justificacion.",
            _build_actionable_gap(
                field="prior_claim_result",
                label="Falta dejar trazabilidad del reclamo previo o explicar por que aun no existe",
                prompt="Cuenta si ya reclamaste al banco, por cual canal y que respondieron, o explica que este sera el primer reclamo.",
                recommended_action=recommended_action,
            ),
        ),
        (
            "En habeas data debe identificarse el dato, reporte o registro cuestionado.",
            _build_actionable_gap(
                field="disputed_data",
                label="Falta identificar el dato o reporte cuestionado",
                prompt="Indica el dato, reporte o registro personal que quieres corregir o eliminar.",
                recommended_action=recommended_action,
            ),
        ),
        (
            "En habeas data debe quedar clara la accion solicitada sobre el dato.",
            _build_actionable_gap(
                field="requested_data_action",
                label="Falta indicar como debe quedar corregido el dato",
                prompt="Indica si debe eliminarse, corregirse, actualizarse o acreditarse con autorizacion.",
                recommended_action=recommended_action,
            ),
        ),
    ]
    existing_gap_keys = {(item.get("field"), item.get("label")) for item in actionable_gaps}
    for issue_text, gap in fallback_gap_rules:
        gap_key = (gap.get("field"), gap.get("label"))
        if issue_text in blocking_issues and gap_key not in existing_gap_keys:
            actionable_gaps.append(gap)
            existing_gap_keys.add(gap_key)

    apto = not blocking_issues and bool(quality_review.get("passed"))
    status = "apto" if apto else "requires_changes"
    next_action = "entregar" if apto else "pedir_mas_datos" if warnings else "corregir"

    return {
        "status": status,
        "apto_para_entrega": apto,
        "blocking_issues": list(dict.fromkeys(blocking_issues)),
        "warnings": list(dict.fromkeys(warnings)),
        "actionable_gaps": list({(item.get("field"), item.get("label")): item for item in actionable_gaps}.values()),
        "quality_score": quality_review.get("score"),
        "citation_guard": citation_guard,
        "next_action": next_action,
        "checks": {
            "tipo_documento_correcto": bool(case.get("recommended_action")),
            "entidad_clara": bool((case.get("routing") or {}).get("primary_target", {}).get("name") or _list(facts.get("entidades_involucradas"))),
            "pretensiones_claras": bool(_text(facts.get("pretension_concreta")) or _has_any(lowered, ["solicito", "pretension", "solicitudes"])),
            "cronologia_minima": bool(_text(facts.get("fechas_mencionadas"))),
            "citas_verificadas": bool(_list(source_policy.get("verified_sources"))),
            "sin_citas_no_verificadas": not citation_guard.get("has_unverified_citations"),
            "sin_promesas_de_resultado": not _has_any(lowered, ["ganaras seguro", "resultado garantizado", "exito asegurado"]),
        },
    }
