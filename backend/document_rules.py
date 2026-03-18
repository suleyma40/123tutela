from __future__ import annotations

from typing import Any


def _normalize(value: str | None) -> str:
    return (
        str(value or "")
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .strip()
    )


DOCUMENT_RULES: dict[str, dict[str, Any]] = {
    "accion de tutela": {
        "document_title": "Accion de tutela",
        "goal": "Proteger de forma inmediata derechos fundamentales amenazados o vulnerados.",
        "required_sections": [
            "competencia y reparto",
            "hechos cronologicos",
            "derechos fundamentales vulnerados",
            "procedencia",
            "pretensiones",
            "pruebas y anexos",
            "juramento de no temeridad",
            "notificaciones",
        ],
        "required_elements": ["hechos", "derechos", "urgencia o procedencia", "pretensiones concretas"],
        "suggested_evidence": ["radicados previos", "historia clinica", "respuestas", "capturas", "facturas"],
        "quality_focus": "cronologia estricta, procedencia y orden concreta al juez",
    },
    "derecho de peticion": {
        "document_title": "Derecho de peticion",
        "goal": "Obtener respuesta de fondo, informacion, documentos o actuacion concreta.",
        "required_sections": [
            "identificacion del peticionario",
            "hechos y contexto",
            "fundamento del derecho de peticion",
            "solicitudes numeradas",
            "termino legal de respuesta",
            "anexos y notificaciones",
        ],
        "required_elements": ["destinatario", "hechos", "solicitudes numeradas", "canal de respuesta"],
        "suggested_evidence": ["radicado previo", "facturas", "correos", "documentos soporte"],
        "quality_focus": "claridad de solicitudes y trazabilidad de la respuesta",
    },
    "queja formal": {
        "document_title": "Queja formal",
        "goal": "Dejar constancia de una irregularidad y pedir intervencion o respuesta institucional.",
        "required_sections": [
            "destinatario",
            "motivo de la queja",
            "hechos verificables",
            "solicitud de intervencion",
            "pruebas y contacto del usuario",
        ],
        "required_elements": ["conducta irregular", "fecha o periodo", "efecto para el usuario", "respuesta esperada"],
        "suggested_evidence": ["capturas", "correos", "radicados", "grabaciones o constancias"],
        "quality_focus": "hecho reprochable bien descrito y peticion institucional clara",
    },
    "reclamo administrativo": {
        "document_title": "Reclamo administrativo",
        "goal": "Exigir correccion, revision o solucion frente a una decision, cobro o actuacion.",
        "required_sections": [
            "destinatario",
            "acto, cobro o decision cuestionada",
            "hechos y cronologia",
            "fundamento del reclamo",
            "correccion solicitada",
            "anexos y notificaciones",
        ],
        "required_elements": ["acto o cobro identificado", "razon del reclamo", "solucion concreta", "soportes"],
        "suggested_evidence": ["facturas", "respuestas previas", "contratos", "capturas"],
        "quality_focus": "error identificado con precision y remedio administrativo ejecutable",
    },
    "reclamacion financiera": {
        "document_title": "Reclamacion financiera",
        "goal": "Solicitar la revision y correccion de un cobro, producto o actuacion financiera no autorizada o improcedente.",
        "required_sections": [
            "destinatario",
            "identificacion del consumidor financiero",
            "hechos y contexto",
            "fundamento del reclamo",
            "solicitudes numeradas",
            "pruebas y anexos",
            "notificaciones",
        ],
        "required_elements": ["destinatario", "hechos", "solicitudes numeradas", "solucion concreta", "canal de respuesta"],
        "suggested_evidence": ["extractos", "pantallazos", "contrato", "chat o correo", "radicado previo"],
        "quality_focus": "hechos verificables, trazabilidad del cobro y peticiones concretas al banco",
    },
    "derecho de peticion financiero": {
        "document_title": "Derecho de peticion financiero",
        "goal": "Obtener respuesta de fondo, informacion y solucion frente a un producto o servicio financiero.",
        "required_sections": [
            "destinatario",
            "identificacion del peticionario",
            "hechos y contexto",
            "fundamento del derecho de peticion",
            "solicitudes numeradas",
            "termino legal de respuesta",
            "anexos y notificaciones",
        ],
        "required_elements": ["destinatario", "hechos", "solicitudes numeradas", "canal de respuesta"],
        "suggested_evidence": ["extractos", "chat o correo", "radicado previo", "contrato"],
        "quality_focus": "solicitudes claras, trazabilidad y termino legal de respuesta",
    },
    "queja disciplinaria": {
        "document_title": "Queja disciplinaria",
        "goal": "Solicitar investigacion disciplinaria por conducta irregular de servidor o funcionario.",
        "required_sections": [
            "autoridad disciplinaria destinataria",
            "identificacion del denunciado",
            "hechos disciplinariamente relevantes",
            "solicitud de investigacion",
            "pruebas, testigos y notificaciones",
        ],
        "required_elements": ["sujeto disciplinable", "cargo o rol", "conducta", "fecha del hecho"],
        "suggested_evidence": ["documentos oficiales", "correos", "respuestas", "testigos"],
        "quality_focus": "conducta atribuible, verificable y con peticion de investigacion seria",
    },
    "accion de cumplimiento": {
        "document_title": "Accion de cumplimiento",
        "goal": "Lograr que una autoridad cumpla una norma o acto administrativo obligatorio.",
        "required_sections": [
            "autoridad accionada",
            "norma o acto incumplido",
            "requerimiento previo",
            "incumplimiento actual",
            "pretensiones de cumplimiento",
            "pruebas y notificaciones",
        ],
        "required_elements": ["deber claro", "autoridad obligada", "requerimiento previo", "incumplimiento concreto"],
        "suggested_evidence": ["acto administrativo", "peticion previa", "respuesta oficial"],
        "quality_focus": "deber expreso y exigible, no simple inconformidad",
    },
    "impugnacion de tutela": {
        "document_title": "Impugnacion de tutela",
        "goal": "Controvertir una decision de tutela que niega o limita la proteccion del derecho.",
        "required_sections": [
            "identificacion del fallo impugnado",
            "hechos relevantes del tramite",
            "errores o desacuerdos con el fallo",
            "solicitud a segunda instancia",
            "pruebas y notificaciones",
        ],
        "required_elements": ["juzgado", "fecha del fallo", "resultado de la decision", "motivos de impugnacion"],
        "suggested_evidence": ["fallo de tutela", "anexos previos", "pruebas nuevas si existen"],
        "quality_focus": "contraargumentar el fallo, no repetir la tutela original sin foco",
    },
    "incidente de desacato": {
        "document_title": "Incidente de desacato",
        "goal": "Poner en conocimiento del juez el incumplimiento de una orden de tutela.",
        "required_sections": [
            "identificacion del fallo de tutela",
            "orden incumplida",
            "hechos posteriores al fallo",
            "solicitud de cumplimiento y sancion",
            "pruebas del incumplimiento",
        ],
        "required_elements": ["juzgado", "fallo", "orden incumplida", "incumplimiento posterior"],
        "suggested_evidence": ["fallo de tutela", "respuestas posteriores", "correos", "constancias"],
        "quality_focus": "orden judicial identificable e incumplimiento probado",
    },
    "carta formal a entidad": {
        "document_title": "Carta formal a entidad",
        "goal": "Dejar constancia, requerir o advertir formalmente a una entidad o empresa.",
        "required_sections": [
            "destinatario",
            "hechos resumidos",
            "solicitud concreta",
            "anexos y datos de contacto",
        ],
        "required_elements": ["destinatario", "hechos", "solicitud"],
        "suggested_evidence": ["soportes basicos del caso"],
        "quality_focus": "tono firme y claro sin fingir una accion distinta",
    },
}


def get_document_rule(recommended_action: str | None, workflow_type: str | None = None) -> dict[str, Any]:
    normalized = _normalize(recommended_action)
    rule = DOCUMENT_RULES.get(normalized)
    if rule:
        return {
            "action_key": normalized,
            **rule,
        }

    fallback_title = recommended_action or workflow_type or "Documento juridico"
    return {
        "action_key": normalized or _normalize(fallback_title),
        "document_title": fallback_title,
        "goal": "Presentar una solicitud juridica clara y accionable.",
        "required_sections": ["hechos", "fundamento", "pretensiones", "pruebas y notificaciones"],
        "required_elements": ["hechos", "pretension concreta"],
        "suggested_evidence": ["documentos soporte del caso"],
        "quality_focus": "claridad, hechos verificables y peticiones ejecutables",
    }


def evaluate_document_rule(
    *,
    recommended_action: str | None,
    workflow_type: str | None,
    description: str,
    facts: dict[str, Any],
) -> dict[str, Any]:
    rule = get_document_rule(recommended_action, workflow_type)
    text = _normalize(description)
    facts_text = _normalize(str(facts.get("hechos_principales") or ""))
    intake = facts.get("intake_form") or {}
    full_text = _normalize(
        " ".join(
            [
                text,
                facts_text,
                str(intake.get("eps_name") or ""),
                str(intake.get("diagnosis") or ""),
                str(intake.get("treatment_needed") or ""),
                str(intake.get("urgency_detail") or ""),
                str(intake.get("medical_order_date") or ""),
                str(intake.get("treating_doctor_name") or ""),
                str(intake.get("eps_request_date") or ""),
                str(intake.get("eps_request_channel") or ""),
                str(intake.get("eps_request_reference") or ""),
                str(intake.get("eps_response_detail") or ""),
                str(intake.get("special_protection") or ""),
                str(intake.get("tutela_special_protection_detail") or ""),
                str(intake.get("ongoing_harm") or ""),
                str(intake.get("tutela_oath_statement") or ""),
                str(intake.get("tutela_no_temperity_detail") or ""),
                str(intake.get("tutela_other_means_detail") or ""),
                str(intake.get("tutela_immediacy_detail") or ""),
            ]
        )
    )
    blocking_issues: list[str] = []
    warnings: list[str] = []

    if not facts.get("entidades_involucradas"):
        blocking_issues.append("Falta identificar claramente el destinatario o sujeto pasivo del documento.")
    if len(facts_text) < 80:
        blocking_issues.append("Los hechos consolidados siguen siendo breves para sostener un documento serio.")
    if "pretension concreta" in rule["required_elements"] and not any(word in full_text for word in ["solicito", "pido", "requiero", "pretendo", "ordenen", "corrijan"]):
        blocking_issues.append("El documento requiere una pretension concreta mejor formulada.")

    action_key = rule["action_key"]
    if action_key == "accion de tutela":
        uploaded_evidence = facts.get("uploaded_evidence_files") or []
        health_tutela_context = (
            _normalize(str(intake.get("category") or facts.get("category") or "")) == "salud"
            or bool(str(intake.get("eps_name") or "").strip())
            or bool(str(intake.get("diagnosis") or "").strip())
        )
        ai_can_infer_health_urgency = health_tutela_context and all(
            str(intake.get(field) or "").strip()
            for field in ("eps_name", "diagnosis", "treatment_needed")
        ) and (
            bool(uploaded_evidence)
            or bool(str(intake.get("medical_order_date") or "").strip())
            or bool(str(intake.get("eps_response_detail") or "").strip())
            or bool(str(intake.get("special_protection") or "").strip())
            or bool(str(intake.get("tutela_special_protection_detail") or "").strip())
        )
        if not any(word in full_text for word in ["no temeridad", "no he presentado otra tutela", "otra tutela", "juramento"]):
            blocking_issues.append("La tutela debe incluir una declaracion de no temeridad o explicar si existio tutela previa.")
        if not ai_can_infer_health_urgency and not any(word in full_text for word in ["otro medio", "subsidiariedad", "perjuicio irremediable", "no existe otro medio eficaz"]):
            blocking_issues.append("La tutela debe justificar subsidiariedad o perjuicio irremediable.")
        if not ai_can_infer_health_urgency and not any(word in full_text for word in ["inmediatez", "reciente", "actualmente", "hoy", "sigue ocurriendo"]):
            blocking_issues.append("La tutela debe explicar por que la vulneracion es actual o por que se cumple la inmediatez.")
        if not ai_can_infer_health_urgency and not any(word in full_text for word in ["urgencia", "riesgo", "perjuicio", "vulneracion", "vulneración", "derecho fundamental"]):
            blocking_issues.append("La tutela necesita dejar mejor descritos los hechos actuales del paciente, la barrera de la EPS y el riesgo que sigue ocurriendo hoy.")
        elif ai_can_infer_health_urgency and not any(word in full_text for word in ["urgencia", "riesgo", "perjuicio", "vulneracion", "vulneración", "derecho fundamental"]):
            warnings.append("La IA debe reforzar internamente la urgencia y procedencia con base en la orden medica, la EPS involucrada y los anexos disponibles.")
        if any(word in full_text for word in ["particular", "empresa privada", "privada", "privado"]) and not any(
            word in full_text
            for word in ["servicio publico", "servicio p?blico", "indefension", "indefensi?n", "subordinacion", "subordinaci?n", "posicion dominante", "posici?n dominante", "articulo 42", "art. 42"]
        ):
            blocking_issues.append("Si la tutela es contra un particular, debe justificarse expresamente el supuesto habilitante del articulo 42 del Decreto 2591 de 1991.")
    elif action_key == "derecho de peticion":
        if not any(word in full_text for word in ["15 dias", "15 días", "10 dias", "10 días", "30 dias", "30 días", "ley 1755"]):
            warnings.append("Conviene incorporar el termino legal de respuesta o la referencia expresa a la Ley 1755 de 2015.")
        if "privada" in full_text and not any(word in full_text for word in ["servicio publico", "servicio público", "interes colectivo", "posicion dominante", "posición dominante"]):
            blocking_issues.append("Si el derecho de peticion va contra un privado, debe explicarse por que ese particular esta obligado a responder.")
        if not any(word in full_text for word in ["1)", "1.", "solicitudes numeradas", "respondan", "informen", "entreguen", "certifiquen"]):
            warnings.append("Conviene reforzar las solicitudes numeradas para que el derecho de peticion sea mas claro.")
    elif action_key == "accion de cumplimiento":
        if not any(word in full_text for word in ["ley", "decreto", "resolucion", "resolución", "acto administrativo"]):
            blocking_issues.append("La accion de cumplimiento exige identificar la norma o el acto incumplido.")
    elif action_key == "impugnacion de tutela":
        if not any(word in full_text for word in ["3 dias", "3 días", "dentro del termino", "dentro del término", "notificacion", "notificación"]):
            blocking_issues.append("La impugnacion debe justificar que se presenta dentro del termino de 3 dias habiles desde la notificacion.")
        if any(word in full_text for word in ["4 dias", "4 d?as", "5 dias", "5 d?as", "6 dias", "6 d?as", "una semana", "7 dias", "7 d?as", "mes pasado", "hace semanas"]):
            blocking_issues.append("La impugnacion parece extemporanea o mal explicada en el termino. Debe revisarse el plazo fatal de 3 dias habiles.")
        if not any(word in full_text for word in ["fallo", "impugno", "segunda instancia", "error del juez", "decision negada"]):
            blocking_issues.append("La impugnacion necesita identificar el fallo y el desacuerdo juridico concreto.")
        if not any(word in full_text for word in ["razon del juez", "razones del juez", "error de valoracion", "error de valoración", "improcedente", "prueba no valorada"]):
            blocking_issues.append("La impugnacion debe contraargumentar al menos una razon concreta del fallo.")
    elif action_key == "incidente de desacato":
        if not any(word in full_text for word in ["juzgado", "despacho", "primera instancia"]):
            blocking_issues.append("El desacato debe identificar el mismo juzgado o despacho de primera instancia que emitio el fallo.")
        if not any(word in full_text for word in ["notificado", "notificacion", "notificación", "se notifico", "se notificó"]):
            blocking_issues.append("El desacato debe explicar que el fallo fue notificado a la entidad o responsable.")
        if not any(word in full_text for word in ["incumplio", "incumplimiento", "orden judicial", "fallo de tutela"]):
            blocking_issues.append("El desacato requiere identificar la orden judicial incumplida y su incumplimiento.")

    return {
        "rule": rule,
        "status": "requires_more_data" if blocking_issues else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }
