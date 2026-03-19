from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _intake_text(facts: dict[str, Any], *keys: str) -> str:
    intake = facts.get("intake_form") or {}
    for key in keys:
        value = _text(intake.get(key))
        if value:
            return value
    return ""


def _health_supports_present(facts: dict[str, Any], combined_text: str) -> bool:
    return bool(
        _intake_text(
            facts,
            "evidence_summary",
            "supporting_documents",
            "medical_order_date",
            "treating_doctor_name",
            "eps_request_reference",
            "eps_request_date",
        )
    ) or _has_any(
        combined_text,
        [
            "orden medica",
            "orden médica",
            "formula",
            "historia clinica",
            "historia clínica",
            "radicado",
            "autorizacion",
            "autorización",
            "correo",
            "captura",
            "pdf",
            "anexo",
            "soporte",
        ],
    )


def _health_current_harm_present(facts: dict[str, Any], combined_text: str) -> bool:
    return bool(_intake_text(facts, "urgency_detail", "current_harm", "ongoing_harm", "tutela_immediacy_detail")) or _has_any(
        combined_text,
        ["urgencia", "riesgo", "dolor", "agrav", "empeor", "suspension", "suspensión", "vida", "tratamiento", "medicamento", "cita", "cirugia", "cirugía"],
    )


def _health_chronology_present(facts: dict[str, Any]) -> bool:
    return bool(
        _text(facts.get("fechas_mencionadas"))
        or _intake_text(facts, "key_dates", "event_date", "event_period_detail", "medical_order_date", "eps_request_date")
    )


def _detect_health_contradictions(*, description: str, facts: dict[str, Any]) -> dict[str, list[str]]:
    problems: list[str] = []
    warnings: list[str] = []

    intake = facts.get("intake_form") or {}
    combined_text = _lower(
        " ".join(
            [
                _text(description),
                _text(facts.get("hechos_principales")),
                _text(intake.get("case_story")),
                _text(intake.get("urgency_detail")),
                _text(intake.get("current_harm")),
                _text(intake.get("ongoing_harm")),
                _text(intake.get("prior_claim_result")),
                _text(intake.get("eps_response_detail")),
                _text(intake.get("tutela_other_means_detail")),
                _text(intake.get("tutela_immediacy_detail")),
                _text(intake.get("tutela_special_protection_detail")),
            ]
        )
    )

    target_entity = _lower(intake.get("target_entity"))
    eps_name = _lower(intake.get("eps_name"))
    prior_claim = _lower(intake.get("prior_claim"))
    prior_claim_detail = _intake_text(facts, "prior_claim_result", "eps_response_detail", "eps_request_date", "eps_request_reference", "tutela_other_means_detail")
    acting_capacity = _lower(intake.get("acting_capacity"))
    represented_name = _text(intake.get("represented_person_name"))
    represented_age = _text(intake.get("represented_person_age") or intake.get("represented_person_birth_date"))
    represented_document = _text(intake.get("represented_person_document"))
    special_protection = _lower(intake.get("special_protection"))
    special_protection_detail = _text(intake.get("tutela_special_protection_detail"))
    urgency_detail = _text(intake.get("urgency_detail") or intake.get("current_harm") or intake.get("ongoing_harm") or intake.get("tutela_immediacy_detail"))

    if target_entity and eps_name and target_entity != eps_name:
        problems.append("La EPS o entidad de salud no es consistente: el formulario menciona nombres distintos entre entidad accionada y EPS.")

    if prior_claim in {"no", "aun no", "aún no", "no_aun_no"} and prior_claim_detail:
        problems.append("La gestion previa es contradictoria: marcaste que no hubo reclamo previo, pero el expediente si describe una solicitud, radicado o respuesta de la EPS.")

    if prior_claim in {"si", "sí", "reclame", "reclamo"} and not prior_claim_detail:
        warnings.append("La gestion previa aparece marcada como realizada, pero falta contar que se pidio a la EPS y que respondio o que barrera impuso.")

    if acting_capacity == "nombre_propio" and (represented_name or represented_age or represented_document):
        warnings.append("La representacion del caso es ambigua: aparecen datos de un menor o representado, pero la calidad del accionante sigue en nombre propio.")

    if acting_capacity and acting_capacity != "nombre_propio" and not represented_name:
        problems.append("La representacion del caso es inconsistente: indicaste que actuas por otra persona, pero falta identificar a quien representas.")

    if acting_capacity and acting_capacity != "nombre_propio" and represented_name and not (represented_age or represented_document):
        warnings.append("La representacion del caso sigue incompleta: conviene precisar edad, fecha de nacimiento o documento del representado.")

    if special_protection in {"no aplica", "ninguno"} and special_protection_detail:
        warnings.append("La proteccion especial es inconsistente: marcaste 'No aplica', pero el relato si describe una condicion de especial proteccion.")

    if special_protection not in {"", "no aplica", "ninguno"} and not special_protection_detail and special_protection not in {"menor de edad"}:
        warnings.append("Conviene explicar mejor por que existe especial proteccion para que ese dato no quede solo como etiqueta.")

    if _has_any(combined_text, ["ya entregaron", "ya autorizaron", "ya resolvieron", "ya agendaron", "solucionado"]) and urgency_detail:
        warnings.append("El relato mezcla una posible solucion ya cumplida con una urgencia actual. Conviene aclarar si el problema ya se resolvio o que parte sigue incumplida hoy.")

    if _has_any(combined_text, ["tutela anterior", "ya presente tutela", "ya presenté tutela", "otra tutela"]) and not _text(intake.get("prior_tutela")) and not _text(intake.get("prior_tutela_reason")):
        warnings.append("El relato sugiere una tutela previa, pero ese dato no quedo estructurado en el expediente.")

    if not urgency_detail and _has_any(combined_text, ["urgente", "urgencia", "riesgo vital", "dolor intenso", "crisis", "hospitalizacion", "hospitalización"]):
        warnings.append("El relato sugiere urgencia, pero falta dejar ese riesgo actual en el campo especifico de urgencia del caso.")

    return {
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_health_stage_readiness(
    *,
    workflow_type: str,
    recommended_action: str,
    description: str,
    facts: dict[str, Any],
    prior_actions: list[str],
    stage: str,
) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []
    contradictions = _detect_health_contradictions(description=description, facts=facts)

    intake = facts.get("intake_form") or {}
    combined_text = _lower(
        " ".join(
            [
                _text(description),
                _text(facts.get("hechos_principales")),
                _text(intake.get("case_story")),
                _text(intake.get("concrete_request")),
                _text(intake.get("key_dates")),
                _text(intake.get("target_entity")),
                _text(intake.get("eps_name")),
                _text(intake.get("diagnosis")),
                _text(intake.get("treatment_needed")),
                _text(intake.get("urgency_detail")),
                _text(intake.get("eps_response_detail")),
                _text(intake.get("prior_claim_result")),
                _text(intake.get("tutela_other_means_detail")),
                _text(intake.get("tutela_immediacy_detail")),
                _text(intake.get("tutela_previous_action_detail")),
                _text(intake.get("tutela_oath_statement")),
            ]
        )
    )

    target_entity = _intake_text(facts, "target_entity", "eps_name")
    diagnosis = _intake_text(facts, "diagnosis")
    treatment_needed = _intake_text(facts, "treatment_needed")
    case_story = _intake_text(facts, "case_story")
    concrete_request = _intake_text(facts, "concrete_request", "numbered_requests")
    current_harm_present = _health_current_harm_present(facts, combined_text)
    chronology_present = _health_chronology_present(facts)
    supports_present = _health_supports_present(facts, combined_text)
    prior_claim_present = bool(
        prior_actions
        or _intake_text(facts, "prior_claim_result", "eps_response_detail", "eps_request_date", "eps_request_reference", "tutela_other_means_detail")
        or _lower(intake.get("prior_claim")) in {"si", "sí", "reclame", "reclamo", "radicado"}
    )
    action = _lower(recommended_action)

    if stage == "preview":
        if not target_entity:
            problems.append("Para analizar un caso de salud hace falta identificar la EPS, IPS o entidad involucrada.")
        if not diagnosis:
            problems.append("Para analizar un caso de salud hace falta el diagnostico o la condicion medica principal.")
        if not treatment_needed:
            problems.append("Para analizar un caso de salud hace falta el servicio, medicamento o procedimiento requerido.")
        if len(_text(description)) < 80 and len(case_story) < 80:
            problems.append("Para el preview de salud hace falta contar mejor que paso y que sigue ocurriendo.")
        if not current_harm_present:
            problems.append("Para el preview de salud hace falta explicar la urgencia, el riesgo o la afectacion actual.")
    elif stage == "save":
        if not target_entity:
            problems.append("En salud debe quedar clara la EPS, IPS o entidad accionada.")
        if not diagnosis:
            problems.append("En salud falta el diagnostico o condicion medica principal.")
        if not treatment_needed:
            problems.append("En salud falta el tratamiento, medicamento o servicio concreto requerido.")
        if not current_harm_present:
            problems.append("En salud falta explicar con mas fuerza la urgencia, el riesgo o el servicio requerido.")
        if not chronology_present:
            problems.append("En salud faltan fechas o referencias temporales minimas para ordenar la cronologia.")
        if not concrete_request:
            problems.append("En salud falta una solicitud concreta o resultado claramente pedido a la entidad.")
        if not supports_present:
            warnings.append("Conviene describir formula, historia clinica, autorizacion, negacion o cualquier soporte medico disponible.")
    elif stage == "generate":
        if "derecho de peticion" in action:
            if not target_entity:
                problems.append("El derecho de peticion en salud necesita una entidad destinataria clara.")
            if not concrete_request:
                problems.append("El derecho de peticion en salud necesita solicitudes concretas y verificables.")
            if len(_text(description)) < 120 and len(case_story) < 120:
                problems.append("El derecho de peticion en salud necesita hechos mas claros antes de generar el documento.")
            if not _intake_text(facts, "response_channel", "copy_email"):
                warnings.append("Conviene definir un canal de respuesta expreso para el derecho de peticion.")
        elif "impugnacion" in action:
            if not _intake_text(facts, "tutela_court_name"):
                problems.append("La impugnacion en salud debe identificar el juzgado o despacho que decidio la tutela.")
            if not _intake_text(facts, "tutela_ruling_date", "tutela_decision_result"):
                problems.append("La impugnacion en salud debe identificar la fecha o decision que se controvierte.")
            if not _intake_text(facts, "tutela_decision_result"):
                problems.append("La impugnacion en salud debe indicar el resultado del fallo de tutela.")
            if not _intake_text(facts, "tutela_appeal_reason"):
                problems.append("La impugnacion en salud debe exponer el motivo concreto de inconformidad.")
        elif "desacato" in action:
            if not _intake_text(facts, "tutela_court_name"):
                problems.append("El desacato en salud debe identificar el juzgado que emitio el fallo.")
            if not _intake_text(facts, "tutela_ruling_date", "tutela_order_summary"):
                problems.append("El desacato en salud debe identificar el fallo y la orden judicial incumplida.")
            if not _intake_text(facts, "tutela_noncompliance_detail"):
                problems.append("El desacato en salud debe explicar con hechos concretos el incumplimiento actual.")
        else:
            if not target_entity:
                problems.append("La tutela en salud necesita una EPS, IPS o entidad accionada claramente identificada.")
            if not diagnosis:
                problems.append("La tutela en salud necesita el diagnostico o condicion medica principal.")
            if not treatment_needed:
                problems.append("La tutela en salud necesita el servicio, medicamento o procedimiento requerido.")
            if not current_harm_present:
                problems.append("La tutela en salud necesita explicar que dano o riesgo sigue ocurriendo hoy.")
            if not prior_claim_present:
                problems.append("La tutela en salud necesita gestion previa clara o explicacion de por que la urgencia no permitia esperar.")
            if not _intake_text(facts, "tutela_immediacy_detail", "urgency_detail"):
                problems.append("La tutela en salud necesita justificar por que la vulneracion es actual o reciente.")
            if not _intake_text(facts, "tutela_previous_action_detail", "prior_tutela", "prior_tutela_reason"):
                problems.append("La tutela en salud necesita aclarar si ya existio otra tutela, peticion o medida previa.")
            if not _intake_text(facts, "tutela_oath_statement", "tutela_no_temperity_detail", "prior_tutela"):
                problems.append("La tutela en salud necesita declaracion o aclaracion suficiente sobre no temeridad.")
            if not supports_present:
                problems.append("La tutela en salud necesita al menos un soporte medico minimo o una descripcion muy concreta del soporte disponible.")

    problems.extend(contradictions.get("blocking_issues") or [])
    warnings.extend(contradictions.get("warnings") or [])

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": list(dict.fromkeys(problems)),
        "warnings": list(dict.fromkeys(warnings)),
    }


def _validate_tutela(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    intake = facts.get("intake_form") or {}
    entities = facts.get("entidades_involucradas") or []
    dates = facts.get("fechas_mencionadas") or []
    problem = _lower(facts.get("problema_central"))
    consolidated_text = _lower(
        " ".join(
            [
                _text(description),
                _text(facts.get("hechos_principales")),
                _text(intake.get("case_story")),
                _text(intake.get("concrete_request")),
                _text(intake.get("key_dates")),
                _text(intake.get("target_entity")),
                _text(intake.get("eps_name")),
                _text(intake.get("diagnosis")),
                _text(intake.get("treatment_needed")),
                _text(intake.get("urgency_detail")),
                _text(intake.get("tutela_previous_action_detail")),
                _text(intake.get("tutela_oath_statement")),
                _text(intake.get("tutela_other_means_detail")),
                _text(intake.get("tutela_immediacy_detail")),
            ]
        )
    )
    target_entity = _intake_text(facts, "target_entity", "eps_name")
    concrete_request = _intake_text(facts, "concrete_request")
    diagnosis = _intake_text(facts, "diagnosis")
    treatment_needed = _intake_text(facts, "treatment_needed")

    if not entities and not target_entity:
        problems.append("Falta identificar con claridad la entidad o persona accionada.")
    if not dates and not _text(intake.get("key_dates")):
        problems.append("Faltan fechas o referencias temporales minimas para construir la cronologia.")
    if len(_text(facts.get("hechos_principales"))) < 80 and len(_text(intake.get("case_story"))) < 80:
        problems.append("Los hechos extraidos son demasiado breves para sustentar una tutela solida.")
    if not _has_any(consolidated_text, ["derecho", "salud", "vida", "minimo vital", "peticion", "urgencia", "riesgo", "afecta", "vulner"]):
        warnings.append("No aparece claramente explicado el derecho afectado o el riesgo actual.")
    if not concrete_request and not _has_any(consolidated_text, ["solicito", "pido", "requiero", "necesito", "pretendo", "ordenen"]):
        warnings.append("No se ve una pretension concreta en el relato del usuario.")
    if (
        not prior_actions
        and not _text(intake.get("tutela_previous_action_detail"))
        and not _text(intake.get("tutela_other_means_detail"))
        and not _has_any(consolidated_text, ["urgencia", "riesgo", "inmediato", "grave", "menor", "embarazada", "discapacidad"])
    ):
        warnings.append("Puede faltar justificacion de via previa o de urgencia para soportar la procedencia de la tutela.")
    if "salud" in problem and not (target_entity and (diagnosis or treatment_needed)) and not _has_any(
        consolidated_text,
        ["eps", "ips", "orden medica", "tratamiento", "cita", "medicamento"],
    ):
        warnings.append("En salud conviene pedir datos de EPS, orden medica o tratamiento para evitar una tutela debil.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_derecho_peticion(description: str, facts: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar la entidad o destinatario del derecho de peticion.")
    if not _has_any(text, ["solicito", "pido", "requiero", "entreguen", "respondan", "informen", "certifiquen"]):
        problems.append("No esta claro que se solicita exactamente en el derecho de peticion.")
    if len(_text(facts.get("hechos_principales"))) < 60:
        warnings.append("Los hechos del derecho de peticion todavia son escasos para soportar una respuesta de fondo.")
    if not _has_any(text, ["respuesta", "informacion", "documento", "copia", "consulta"]):
        warnings.append("Conviene precisar mejor el tipo de peticion para ajustar el termino legal de respuesta.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_habeas_data(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar la entidad o base de datos que trata la informacion.")
    if not _has_any(text, ["dato", "reporte", "historial", "datacredito", "cifin", "informacion"]):
        problems.append("No se identifica con claridad cual es el dato o reporte cuestionado.")
    if not _has_any(text, ["corregir", "actualizar", "eliminar", "suprimir", "rectificar"]):
        problems.append("Debe quedar claro si se pide corregir, actualizar o suprimir el dato.")
    if not prior_actions and not _has_any(text, ["reclamo previo", "reclamacion previa", "radicado", "peticion previa", "derecho de peticion"]):
        problems.append("En habeas data debe existir o describirse una reclamacion previa ante la fuente o responsable del tratamiento.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_laboral(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar el empleador o la entidad contra la que se formula la solicitud.")
    if not _has_any(text, ["relacion laboral", "contrato", "empleador", "cargo", "prestacion de servicios"]):
        problems.append("Debe explicarse el tipo de relacion laboral o contractual del caso.")
    if not _has_any(text, ["despido", "sancion", "salario", "liquidacion", "medida", "suspension", "acoso", "incapacidad"]):
        problems.append("No se identifica con claridad la medida, incumplimiento o afectacion laboral principal.")
    if not _has_any(text, ["minimo vital", "salud", "embarazo", "discapacidad", "fuero", "estabilidad reforzada"]):
        warnings.append("Conviene precisar si existe afectacion al minimo vital o alguna condicion de estabilidad reforzada.")
    if not prior_actions:
        warnings.append("En laboral suele convenir dejar trazabilidad de reclamo previo al empleador salvo urgencia constitucional.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_bancos(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar el banco, la fintech o la central de riesgo involucrada.")
    if not _has_any(text, ["credito", "tarjeta", "cuenta", "nequi", "daviplata", "producto financiero"]):
        problems.append("Debe identificarse el producto financiero o la relacion bancaria afectada.")
    if not _has_any(text, ["cobro", "mora", "bloqueo", "reporte", "fraude", "debito", "suplantacion"]):
        problems.append("No se identifica con claridad el cobro, reporte, bloqueo o hecho bancario controvertido.")
    if not _has_any(text, ["valor", "monto", "$", "pesos"]):
        warnings.append("Conviene indicar el monto, cuota o valor discutido para que el reclamo no quede vago.")
    if not prior_actions and not _has_any(text, ["reclamo previo", "reclamacion previa", "radicado", "pqrs", "derecho de peticion"]):
        problems.append("En conflictos bancarios y financieros debe existir o describirse una reclamacion previa antes de escalar.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_servicios(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar la empresa de servicios o telecomunicaciones involucrada.")
    if not _has_any(text, ["agua", "luz", "energia", "gas", "internet", "telefono", "telefonia", "servicio"]):
        problems.append("Debe precisarse el servicio afectado para definir la ruta correcta.")
    if not _has_any(text, ["corte", "suspension", "factura", "facturacion", "reconexion", "cobro", "cobro indebido"]):
        problems.append("No se identifica con claridad el corte, la suspension o la facturacion discutida.")
    if not _has_any(text, ["suscriptor", "contrato", "referencia", "cuenta"]):
        warnings.append("Conviene incluir numero de suscriptor, contrato o referencia del servicio.")
    if not prior_actions and not _has_any(text, ["reclamo previo", "reclamacion previa", "radicado", "pqrs", "peticion previa"]):
        problems.append("En servicios publicos debe existir o describirse reclamacion previa ante la empresa, salvo urgencia constitucional.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_consumidor(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    text = _lower(description)

    if not entities:
        problems.append("Falta identificar el proveedor, comercio o plataforma involucrada.")
    if not _has_any(text, ["producto", "servicio", "compra", "pedido", "garantia", "devolucion"]):
        problems.append("Debe explicarse mejor el producto o servicio y la falla principal del caso.")
    if not _has_any(text, ["cambio", "devolucion", "reembolso", "cumplimiento", "garantia"]):
        problems.append("No se identifica con claridad el remedio que se exige al proveedor.")
    if not _has_any(text, ["factura", "pedido", "orden", "compra", "fecha"]):
        warnings.append("Conviene incluir fecha de compra, numero de pedido o soporte de la transaccion.")
    if not prior_actions and not _has_any(text, ["reclamo previo", "reclamacion previa", "radicado", "garantia radicada", "peticion previa"]):
        problems.append("En consumo debe existir o describirse una reclamacion directa previa al proveedor antes de escalar el conflicto.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_queja_formal(description: str) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []
    text = _lower(description)

    if not _has_any(text, ["motivo principal de la queja", "queja", "irregularidad", "mala atencion", "incumplimiento"]):
        problems.append("La queja formal debe precisar la irregularidad o mala atencion denunciada.")
    if not _has_any(text, ["respuesta o intervencion esperada", "investigacion", "correccion", "traslado"]):
        problems.append("La queja formal debe decir que intervencion o respuesta institucional se espera.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_reclamo_administrativo(description: str) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []
    text = _lower(description)

    if not _has_any(text, ["error administrativo cuestionado", "actuacion", "cobro", "factura", "decision", "respuesta"]):
        problems.append("El reclamo administrativo debe identificar el error, cobro o actuacion que se controvierte.")
    if not _has_any(text, ["correccion administrativa solicitada", "anular", "corregir", "devolver", "responder de fondo", "levantar reporte"]):
        problems.append("El reclamo administrativo debe concretar la correccion o solucion exigida.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_queja_disciplinaria(description: str) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []
    text = _lower(description)

    if not _has_any(text, ["funcionario o sujeto disciplinable", "funcionario", "servidor publico", "inspector", "secretario"]):
        problems.append("La queja disciplinaria debe identificar a quien se denuncia.")
    if not _has_any(text, ["cargo o rol del sujeto disciplinable", "cargo", "rol", "dependencia"]):
        problems.append("La queja disciplinaria debe precisar el cargo o rol del sujeto denunciado.")
    if not _has_any(text, ["conducta disciplinaria denunciada", "omision", "abuso", "irregularidad", "retardo injustificado"]):
        problems.append("La queja disciplinaria debe describir la conducta irregular denunciada.")
    if not _has_any(text, ["fecha de la conducta o hecho disciplinario", "fecha"]):
        warnings.append("Conviene precisar la fecha del hecho disciplinario para que la queja sea trazable.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_accion_cumplimiento(description: str) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []
    text = _lower(description)

    if not _has_any(text, ["norma o acto incumplido", "ley", "decreto", "resolucion", "acto administrativo"]):
        problems.append("La accion de cumplimiento debe identificar la norma o acto administrativo incumplido.")
    if not _has_any(text, ["autoridad obligada a cumplir", "alcaldia", "gobernacion", "secretaria", "entidad"]):
        problems.append("La accion de cumplimiento debe indicar la autoridad obligada a cumplir.")
    if not _has_any(text, ["requerimiento previo realizado", "peticion", "requerimiento", "solicitud previa"]):
        problems.append("La accion de cumplimiento debe dejar rastro del requerimiento previo realizado.")
    if not _has_any(text, ["forma concreta del incumplimiento", "incumplimiento", "no ha cumplido", "se niega a cumplir"]):
        problems.append("La accion de cumplimiento debe explicar concretamente como persiste el incumplimiento.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_impugnacion_tutela(description: str) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []
    text = _lower(description)

    if not _has_any(text, ["juzgado o despacho", "juzgado", "tribunal", "despacho"]):
        problems.append("La impugnacion debe identificar el juzgado o despacho que decidio la tutela.")
    if not _has_any(text, ["fecha del fallo o decision", "fecha del fallo", "decision de tutela"]):
        problems.append("La impugnacion debe identificar la fecha o la decision que se controvierte.")
    if not _has_any(text, ["resultado de la decision de tutela", "negada", "improcedente", "parcialmente"]):
        problems.append("La impugnacion debe indicar el resultado del fallo de tutela.")
    if not _has_any(text, ["motivos de impugnacion", "error", "valoracion", "omision"]):
        problems.append("La impugnacion debe exponer motivos concretos de desacuerdo con el fallo.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def _validate_incidente_desacato(description: str) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []
    text = _lower(description)

    if not _has_any(text, ["juzgado o despacho de tutela", "juzgado", "despacho"]):
        problems.append("El desacato debe identificar el juzgado que emitio el fallo de tutela.")
    if not _has_any(text, ["fecha del fallo de tutela", "fallo de tutela"]):
        problems.append("El desacato debe identificar el fallo de tutela incumplido.")
    if not _has_any(text, ["orden judicial incumplida", "orden", "autorizar", "entregar", "responder"]):
        problems.append("El desacato debe describir la orden judicial incumplida.")
    if not _has_any(text, ["detalle del incumplimiento", "incumplimiento", "no ha cumplido", "sigue sin cumplir"]):
        problems.append("El desacato debe explicar con hechos concretos como persiste el incumplimiento.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def validate_submission_readiness(
    *,
    category: str,
    workflow_type: str = "",
    recommended_action: str = "",
    description: str,
    facts: dict[str, Any],
    prior_actions: list[str],
    stage: str = "save",
) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    text = _text(description)
    facts_text = _text(facts.get("hechos_principales"))
    entities = facts.get("entidades_involucradas") or []
    dates = facts.get("fechas_mencionadas") or []
    category_lower = _lower(category)
    intake = facts.get("intake_form") or {}
    combined_text = _lower(
        " ".join(
            [
                text,
                facts_text,
                _text(intake.get("case_story")),
                _text(intake.get("concrete_request")),
                _text(intake.get("key_dates")),
                _text(intake.get("target_entity")),
                _text(intake.get("eps_name")),
                _text(intake.get("diagnosis")),
                _text(intake.get("treatment_needed")),
                _text(intake.get("urgency_detail")),
                _text(intake.get("tutela_previous_action_detail")),
                _text(intake.get("tutela_oath_statement")),
                _text(intake.get("tutela_other_means_detail")),
                _text(intake.get("tutela_immediacy_detail")),
            ]
        )
    )

    if category_lower == "salud":
        return _validate_health_stage_readiness(
            workflow_type=workflow_type,
            recommended_action=recommended_action,
            description=description,
            facts=facts,
            prior_actions=prior_actions,
            stage=stage,
        )

    if len(text) < 220 and len(_text(intake.get("case_story"))) < 220:
        problems.append("La descripcion consolidada todavia es demasiado corta para sostener un analisis juridico serio.")
    if len(facts_text) < 80 and len(_text(intake.get("case_story"))) < 80:
        problems.append("Los hechos extraidos siguen siendo insuficientes o demasiado breves.")
    if not entities and not _intake_text(facts, "target_entity", "eps_name"):
        problems.append("Falta una entidad, autoridad o destinatario claramente identificable.")
    if not dates and not _text(intake.get("key_dates")):
        problems.append("Faltan fechas o referencias temporales minimas para ordenar la cronologia.")
    if not _text(intake.get("concrete_request")) and not _has_any(
        combined_text,
        ["solicito", "pido", "requiero", "pretendo", "necesito", "ordenen", "respondan", "entreguen", "corrijan"],
    ):
        problems.append("No se identifica una solicitud concreta o pretension claramente formulada.")

    if not _text(intake.get("evidence_summary")) and not _has_any(
        combined_text,
        ["anexo", "soporte", "prueba", "adjunto", "historia clinica", "factura", "correo", "respuesta", "captura", "radicado", "documento"],
    ):
        warnings.append("Conviene describir mejor los soportes o pruebas disponibles para fortalecer el documento.")

    if category_lower == "salud" and not (
        _text(intake.get("urgency_detail"))
        or _has_any(combined_text, ["urgencia", "riesgo", "dolor", "agrav", "tratamiento", "medicamento", "cita", "cirugia", "procedimiento"])
    ):
        problems.append("En casos de salud falta explicar con mas fuerza la urgencia, el riesgo o el servicio requerido.")
    if category_lower == "salud":
        if not _text(intake.get("diagnosis")):
            problems.append("En salud falta el diagnostico o condicion medica principal.")
        if not _text(intake.get("treatment_needed")):
            problems.append("En salud falta el tratamiento, medicamento o servicio concreto requerido.")
        if not _text(intake.get("target_entity")) and not _text(intake.get("eps_name")):
            problems.append("En salud debe quedar clara la EPS, IPS o entidad accionada.")

    if category_lower in {"laboral", "bancos", "servicios", "consumidor"} and not (
        _text(intake.get("numbered_requests")) or _has_any(combined_text, ["1)", "1.", "primero", "segundo", "solicitudes numeradas", "responder", "entregar", "corregir"])
    ):
        warnings.append("En rutas de peticion conviene dejar mas claras las solicitudes numeradas o la respuesta esperada.")

    if category_lower == "datos" and not (
        _text(intake.get("requested_data_action")) or _has_any(combined_text, ["corregir", "actualizar", "suprimir", "eliminar", "rectificar"])
    ):
        problems.append("En habeas data debe quedar clara la accion exacta que se pide sobre el dato.")
    if category_lower == "datos":
        if not _text(intake.get("disputed_data")):
            problems.append("En habeas data debe identificarse el dato o reporte cuestionado.")
        if not _text(intake.get("requested_data_action")):
            problems.append("En habeas data debe definirse si se pide corregir, actualizar o suprimir la informacion.")
    if category_lower == "bancos":
        if not _text(intake.get("bank_product_type")):
            problems.append("En bancos debe identificarse el producto financiero afectado.")
        if not _text(intake.get("disputed_charge")):
            problems.append("En bancos debe identificarse el cobro, seguro o cargo discutido.")
        if not _text(intake.get("concrete_request")):
            problems.append("En bancos debe quedar clara la devolucion, reverso, cancelacion o correccion solicitada.")
    if "derecho de peticion" in _lower(str((facts.get("dx_result") or {}).get("recommended_document") or "")):
        if not _text(intake.get("numbered_requests")) and not _text(intake.get("concrete_request")):
            problems.append("El derecho de peticion necesita solicitudes numeradas y verificables.")
        if not _text(intake.get("response_channel")) and not _text(intake.get("copy_email")):
            warnings.append("Conviene definir un canal de respuesta expreso para el derecho de peticion.")
    if "accion de tutela" in _lower(str((facts.get("dx_result") or {}).get("recommended_document") or "")):
        if not _text(intake.get("tutela_other_means_detail")):
            problems.append("La tutela necesita justificar subsidiariedad o explicar por que no existe otro medio eficaz.")
        if not _text(intake.get("tutela_immediacy_detail")):
            problems.append("La tutela necesita explicar por que la vulneracion es actual o reciente.")
        if not _text(intake.get("tutela_previous_action_detail")):
            problems.append("La tutela necesita aclarar si ya existio otra tutela, peticion o medida previa sobre los mismos hechos.")
        if not _text(intake.get("tutela_oath_statement")) and not _text(intake.get("tutela_no_temperity_detail")):
            problems.append("La tutela necesita declaracion bajo juramento de no temeridad.")
        if _text(intake.get("acting_capacity")) and _lower(intake.get("acting_capacity")) != "nombre_propio":
            if not _text(intake.get("represented_person_name")):
                problems.append("Si actuas por otra persona, debes identificar el nombre del menor o representado.")
            if not _text(intake.get("represented_person_age")):
                problems.append("Si actuas por otra persona, debes indicar edad o fecha de nacimiento del representado.")

    if not prior_actions and category_lower in {"datos", "laboral", "bancos", "servicios", "consumidor"}:
        warnings.append("No se reporta gestion previa. Revisa si primero debe agotarse peticion o reclamacion formal.")

    return {
        "status": "requires_more_data" if problems else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": problems,
        "warnings": warnings,
    }


def validate_intake(
    *,
    category: str,
    workflow_type: str,
    recommended_action: str,
    description: str,
    facts: dict[str, Any],
    prior_actions: list[str],
) -> dict[str, Any]:
    action = _lower(recommended_action)
    category_lower = _lower(category)

    if "incidente de desacato" in action:
        return _validate_incidente_desacato(description)
    if "impugnacion de tutela" in action:
        return _validate_impugnacion_tutela(description)
    if "accion de cumplimiento" in action:
        return _validate_accion_cumplimiento(description)
    if "queja disciplinaria" in action:
        return _validate_queja_disciplinaria(description)
    if "queja formal" in action:
        return _validate_queja_formal(description)
    if "reclamo administrativo" in action or "reclamacion financiera" in action or "reclamacion por servicios publicos" in action or "reclamo de consumo" in action:
        return _validate_reclamo_administrativo(description)
    if "tutela" in action or workflow_type == "tutela":
        return _validate_tutela(description, facts, prior_actions)
    if category_lower == "laboral":
        return _validate_laboral(description, facts, prior_actions)
    if category_lower == "bancos":
        return _validate_bancos(description, facts, prior_actions)
    if category_lower == "servicios":
        return _validate_servicios(description, facts, prior_actions)
    if category_lower == "consumidor":
        return _validate_consumidor(description, facts, prior_actions)
    if "peticion" in action:
        return _validate_derecho_peticion(description, facts)
    if "habeas" in action or category_lower == "datos":
        return _validate_habeas_data(description, facts, prior_actions)

    return {"status": "not_scored", "blocking_issues": [], "warnings": []}
