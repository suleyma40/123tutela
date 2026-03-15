from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _validate_tutela(description: str, facts: dict[str, Any], prior_actions: list[str]) -> dict[str, Any]:
    problems: list[str] = []
    warnings: list[str] = []

    entities = facts.get("entidades_involucradas") or []
    dates = facts.get("fechas_mencionadas") or []
    problem = _lower(facts.get("problema_central"))
    text = _lower(description)

    if not entities:
      problems.append("Falta identificar con claridad la entidad o persona accionada.")
    if not dates:
      problems.append("Faltan fechas o referencias temporales mínimas para construir la cronología.")
    if len(_text(facts.get("hechos_principales"))) < 80:
      problems.append("Los hechos extraídos son demasiado breves para sustentar una tutela sólida.")
    if not _has_any(text, ["derecho", "salud", "vida", "mínimo vital", "minimo vital", "petición", "peticion", "urgencia", "riesgo", "afecta", "vulner"]):
      warnings.append("No aparece claramente explicado el derecho afectado o el riesgo actual.")
    if not _has_any(text, ["solicito", "pido", "requiero", "necesito", "pretendo", "ordenen"]):
      warnings.append("No se ve una pretensión concreta en el relato del usuario.")
    if not prior_actions and not _has_any(text, ["urgencia", "riesgo", "inmediato", "grave", "menor", "embarazada", "discapacidad"]):
      warnings.append("Puede faltar justificación de vía previa o de urgencia para soportar la procedencia de la tutela.")
    if "salud" in problem and not _has_any(text, ["eps", "ips", "orden médica", "orden medica", "tratamiento", "cita", "medicamento"]):
      warnings.append("En salud conviene pedir datos de EPS, orden médica o tratamiento para evitar una tutela débil.")

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
        problems.append("Falta identificar la entidad o destinatario del derecho de petición.")
    if not _has_any(text, ["solicito", "pido", "requiero", "entreguen", "respondan", "informen", "certifiquen"]):
        problems.append("No está claro qué se solicita exactamente en el derecho de petición.")
    if len(_text(facts.get("hechos_principales"))) < 60:
        warnings.append("Los hechos del derecho de petición todavía son escasos para soportar una respuesta de fondo.")
    if not _has_any(text, ["respuesta", "información", "informacion", "documento", "copia", "consulta"]):
        warnings.append("Conviene precisar mejor el tipo de petición para ajustar el término legal de respuesta.")

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
        problems.append("Falta identificar la entidad o base de datos que trata la información.")
    if not _has_any(text, ["dato", "reporte", "historial", "datacredito", "cifin", "información", "informacion"]):
        problems.append("No se identifica con claridad cuál es el dato o reporte cuestionado.")
    if not _has_any(text, ["corregir", "actualizar", "eliminar", "suprimir", "rectificar"]):
        problems.append("Debe quedar claro si se pide corregir, actualizar o suprimir el dato.")
    if not prior_actions:
        warnings.append("Conviene validar si ya hubo reclamación previa ante la fuente o responsable del tratamiento.")

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
    if not _has_any(text, ["minimo vital", "mÃ­nimo vital", "salud", "embarazo", "discapacidad", "fuero", "estabilidad reforzada"]):
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
    if not _has_any(text, ["cobro", "mora", "bloqueo", "reporte", "fraude", "debito", "suplantacion", "suplantaciÃ³n"]):
        problems.append("No se identifica con claridad el cobro, reporte, bloqueo o hecho bancario controvertido.")
    if not _has_any(text, ["valor", "monto", "$", "pesos"]):
        warnings.append("Conviene indicar el monto, cuota o valor discutido para que el reclamo no quede vago.")
    if not prior_actions:
        warnings.append("En bancos y habeas data suele exigirse reclamacion previa antes de escalar a tutela.")

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
    if not prior_actions:
        warnings.append("En servicios publicos conviene dejar constancia de reclamacion previa ante la empresa.")

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
    if not _has_any(text, ["producto", "servicio", "compra", "pedido", "garantia", "garantÃ­a", "devolucion", "devoluciÃ³n"]):
        problems.append("Debe explicarse mejor el producto o servicio y la falla principal del caso.")
    if not _has_any(text, ["cambio", "devolucion", "devoluciÃ³n", "reembolso", "cumplimiento", "garantia", "garantÃ­a"]):
        problems.append("No se identifica con claridad el remedio que se exige al proveedor.")
    if not _has_any(text, ["factura", "pedido", "orden", "compra", "fecha"]):
        warnings.append("Conviene incluir fecha de compra, numero de pedido o soporte de la transaccion.")
    if not prior_actions:
        warnings.append("En consumo es mejor dejar trazabilidad de reclamacion directa antes de escalar el conflicto.")

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
    lowered = _lower(description)
    facts_text = _text(facts.get("hechos_principales"))
    entities = facts.get("entidades_involucradas") or []
    dates = facts.get("fechas_mencionadas") or []
    category_lower = _lower(category)

    if len(text) < 220:
        problems.append("La descripcion consolidada todavia es demasiado corta para sostener un analisis juridico serio.")
    if len(facts_text) < 80:
        problems.append("Los hechos extraidos siguen siendo insuficientes o demasiado breves.")
    if not entities:
        problems.append("Falta una entidad, autoridad o destinatario claramente identificable.")
    if not dates:
        problems.append("Faltan fechas o referencias temporales minimas para ordenar la cronologia.")
    if not _has_any(lowered, ["solicito", "pido", "requiero", "pretendo", "necesito", "ordenen", "respondan", "entreguen", "corrijan"]):
        problems.append("No se identifica una solicitud concreta o pretension claramente formulada.")

    if not _has_any(lowered, ["anexo", "soporte", "prueba", "adjunto", "historia clinica", "factura", "correo", "respuesta", "captura", "radicado", "documento"]):
        warnings.append("Conviene describir mejor los soportes o pruebas disponibles para fortalecer el documento.")

    if category_lower == "salud" and not _has_any(lowered, ["urgencia", "riesgo", "dolor", "agrav", "tratamiento", "medicamento", "cita", "cirugia", "procedimiento"]):
        problems.append("En casos de salud falta explicar con mas fuerza la urgencia, el riesgo o el servicio requerido.")

    if category_lower in {"laboral", "bancos", "servicios", "consumidor"} and not _has_any(lowered, ["1)", "1.", "primero", "segundo", "solicitudes numeradas", "responder", "entregar", "corregir"]):
        warnings.append("En rutas de peticion conviene dejar mas claras las solicitudes numeradas o la respuesta esperada.")

    if category_lower == "datos" and not _has_any(lowered, ["corregir", "actualizar", "suprimir", "eliminar", "rectificar"]):
        problems.append("En habeas data debe quedar clara la accion exacta que se pide sobre el dato.")

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
