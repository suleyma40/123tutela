from __future__ import annotations

from typing import Any


OFFICIAL_SOURCES = [
    {
        "level": 1,
        "label": "Fuentes oficiales obligatorias",
        "sources": [
            "Corte Constitucional",
            "Corte Suprema de Justicia",
            "Consejo de Estado",
            "SUIN-Juriscol",
            "Funcion Publica",
            "Ministerios y superintendencias competentes segun el caso",
            "Leyes, decretos y resoluciones vigentes",
        ],
    },
    {
        "level": 2,
        "label": "Fuentes secundarias permitidas",
        "sources": [
            "Conceptos doctrinales",
            "Articulos juridicos",
            "Guias institucionales",
        ],
    },
    {
        "level": 3,
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
        warnings.append("Conviene explicar con mayor fuerza la urgencia, gravedad o dano actual.")

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
        warnings.append("Hay sujeto de especial proteccion; esto fortalece urgencia y procedencia si se documenta bien.")

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
    text = _lower(description)
    intake = facts.get("intake_form") or {}
    questions: list[dict[str, Any]] = []
    category_lower = _lower(category)

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
                prompt="Que quieres exactamente que ordene la entidad o el juez?",
                reason="No hay una pretension suficientemente concreta.",
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
        if not _text(intake.get("prior_claim_date")) and _lower(intake.get("prior_claim")) in {"si", "sí", "reclame", "reclamo"}:
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
        if (not prior_actions and _lower(intake.get("prior_claim")) not in {"si", "sí", "reclame", "reclamo"}) or not _text(intake.get("prior_claim_result")):
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
        if not _has_any(text, ["devolver a", "consignar", "cuenta de devolucion", "reintegrar"]):
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
                    prompt="Que quieres que haga la entidad con ese dato: corregirlo, actualizarlo, suprimirlo o probar autorizacion?",
                    reason="En habeas data debe definirse la accion exacta sobre la informacion.",
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
                    prompt="Tu peticion es de informacion, documentos, consulta, interes particular o interes general?",
                    reason="Debemos identificar la modalidad del derecho de peticion.",
                    priority="media",
                    field="request_type",
                    route="A",
                )
            )
        if not _text(intake.get("numbered_requests")):
            questions.append(
                _build_question(
                    question_id="solicitudes_numeradas",
                    prompt="Puedes separar en 2 o 3 solicitudes numeradas exactamente lo que esperas que te respondan?",
                    reason="El derecho de peticion necesita solicitudes claras y numeradas.",
                    priority="alta",
                    field="numbered_requests",
                    route="B",
                )
            )

    if workflow_type == "tutela":
        procedencia = evaluate_tutela_procedencia(description=description, facts=facts, prior_actions=prior_actions)
        if procedencia["subscores"]["subsidiariedad"] != "alta":
            questions.append(
                _build_question(
                    question_id="subsidiariedad",
                    prompt="Que gestion previa hiciste y por que no existe otro medio eficaz para protegerte?",
                    reason="La tutela necesita justificar subsidiariedad.",
                    priority="alta",
                    field="subsidiarity_support",
                    route="B",
                )
            )
        if procedencia["subscores"]["temeridad"] == "media":
            questions.append(
                _build_question(
                    question_id="temeridad",
                    prompt="Ya presentaste otra tutela por los mismos hechos? Si si, explica que paso.",
                    reason="Debemos descartar temeridad antes de redactar.",
                    priority="alta",
                    field="prior_tutela_reason",
                    route="B",
                )
            )
        if procedencia["subscores"]["inmediatez"] != "alta":
            questions.append(
                _build_question(
                    question_id="inmediatez",
                    prompt="Por que el problema sigue ocurriendo hoy o por que la tutela sigue siendo urgente?",
                    reason="La inmediatez constitucional aun no queda fuerte.",
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
    pending_questions = facts.get("pending_questions") or []
    high_priority_questions = [item for item in pending_questions if item.get("priority") == "alta"]
    route = ((case.get("routing") or {}).get("case_route") or (facts.get("dx_result") or {}).get("route") or "").strip()

    if not _text(case.get("recommended_action")):
        blocking_issues.append("No esta claramente definido el tipo de accion o documento.")

    if not _text((case.get("routing") or {}).get("primary_target", {}).get("name")) and not _list(facts.get("entidades_involucradas")):
        blocking_issues.append("La entidad accionada o destinataria no quedo suficientemente clara.")

    if not _text(facts.get("pretension_concreta")) and not _has_any(lowered, ["solicito", "pretension", "solicitudes"]):
        blocking_issues.append("Las pretensiones no corresponden claramente al caso o siguen siendo vagas.")
    if route and route != "A":
        blocking_issues.append("El expediente aun no esta en ruta automatizable. Debe completar preguntas o pasar revision previa antes de entregar.")
    if high_priority_questions:
        blocking_issues.append("Faltan datos criticos del caso antes de entregar el documento final.")

    if not _text(facts.get("fechas_mencionadas")):
        warnings.append("La cronologia sigue debil porque faltan fechas o periodos claros.")

    source_policy = facts.get("source_validation_policy") or {}
    if not _list(source_policy.get("verified_sources")) and _has_any(recommended_action, ["tutela", "impugnacion", "desacato", "cumplimiento"]):
        warnings.append("No hay fuentes verificadas cargadas todavia; el sustento jurisprudencial debe mantenerse conservador.")
    if source_policy.get("unresolved_precedents"):
        warnings.append(
            "Existen referencias jurisprudenciales no verificadas automaticamente y fueron excluidas como sustento principal."
        )

    if _has_any(lowered, ["ganaras seguro", "resultado garantizado", "ganara el proceso", "exito asegurado"]):
        blocking_issues.append("El documento promete resultados o contiene afirmaciones impropias.")
    if _has_any(lowered, ["t-760", "t-025", "su-", "c-"]) and not _list(source_policy.get("verified_precedents")):
        blocking_issues.append("El documento menciona jurisprudencia sin soporte verificado suficiente.")

    if "accion de tutela" in recommended_action:
        if _text(intake.get("acting_capacity")) and _lower(intake.get("acting_capacity")) != "nombre_propio":
            if not _text(intake.get("represented_person_name")):
                blocking_issues.append("La tutela debe identificar con claridad a la persona representada o al menor afectado.")
            if not _text(intake.get("represented_person_age")):
                blocking_issues.append("La tutela debe indicar la edad o fecha de nacimiento de la persona representada.")
        if not _text(intake.get("tutela_other_means_detail")):
            blocking_issues.append("La tutela debe justificar subsidiariedad o la insuficiencia de otros medios.")
        if not _text(intake.get("tutela_immediacy_detail")):
            blocking_issues.append("La tutela debe justificar la inmediatez con hechos concretos.")
        if not _text(intake.get("tutela_no_temperity_detail")):
            blocking_issues.append("La tutela debe contener una declaracion clara sobre no temeridad o tutela previa.")
        if _lower(case.get("categoria")) == "salud":
            if not _text(intake.get("target_entity")):
                blocking_issues.append("En tutela de salud debe quedar claramente identificada la EPS o IPS accionada.")
            if not _text(intake.get("diagnosis")):
                blocking_issues.append("En tutela de salud falta el diagnostico o condicion medica principal.")
            if not _text(intake.get("treatment_needed")):
                blocking_issues.append("En tutela de salud falta el medicamento, examen o servicio concreto requerido.")
            if not _text(intake.get("urgency_detail")):
                blocking_issues.append("En tutela de salud falta explicar la urgencia o el riesgo clinico actual.")
    if "derecho de peticion" in recommended_action:
        if not _text(intake.get("numbered_requests")):
            blocking_issues.append("El derecho de peticion debe dejar solicitudes numeradas y verificables.")
        if not _text(intake.get("response_channel")) and not _text(intake.get("copy_email")):
            blocking_issues.append("El derecho de peticion debe indicar un canal de notificacion claro.")
        if _lower(intake.get("petition_target_nature")) == "privada" and not _text(intake.get("petition_private_ground")):
            blocking_issues.append("Si la peticion se dirige a un particular, debe explicarse el fundamento juridico para exigir respuesta.")
    if "reclamacion financiera" in recommended_action:
        if not _text(intake.get("bank_product_type")):
            blocking_issues.append("La reclamacion financiera debe identificar el producto bancario o financiero afectado.")
        if not _text(intake.get("disputed_charge")):
            blocking_issues.append("La reclamacion financiera debe identificar el cobro, seguro o cargo discutido.")
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

    if quality_review.get("blocking_issues"):
        blocking_issues.extend(quality_review["blocking_issues"])

    apto = not blocking_issues and bool(quality_review.get("passed"))
    status = "apto" if apto else "requires_changes"
    next_action = "entregar" if apto else "pedir_mas_datos" if warnings else "corregir"

    return {
        "status": status,
        "apto_para_entrega": apto,
        "blocking_issues": list(dict.fromkeys(blocking_issues)),
        "warnings": list(dict.fromkeys(warnings)),
        "quality_score": quality_review.get("score"),
        "next_action": next_action,
        "checks": {
            "tipo_documento_correcto": bool(case.get("recommended_action")),
            "entidad_clara": bool((case.get("routing") or {}).get("primary_target", {}).get("name") or _list(facts.get("entidades_involucradas"))),
            "pretensiones_claras": bool(_text(facts.get("pretension_concreta")) or _has_any(lowered, ["solicito", "pretension", "solicitudes"])),
            "cronologia_minima": bool(_text(facts.get("fechas_mencionadas"))),
            "citas_verificadas": bool(_list(source_policy.get("verified_sources"))),
            "sin_promesas_de_resultado": not _has_any(lowered, ["ganaras seguro", "resultado garantizado", "exito asegurado"]),
        },
    }
