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
    description: str,
    facts: dict[str, Any],
    prior_actions: list[str],
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
