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
    full_text = f"{text} {facts_text}"
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
        if not any(word in full_text for word in ["urgencia", "riesgo", "perjuicio", "vulneracion", "vulneración", "derecho fundamental"]):
            blocking_issues.append("La tutela necesita explicar urgencia, vulneracion o procedencia con mas fuerza.")
    elif action_key == "derecho de peticion":
        if not any(word in full_text for word in ["1)", "1.", "solicitudes numeradas", "respondan", "informen", "entreguen", "certifiquen"]):
            warnings.append("Conviene reforzar las solicitudes numeradas para que el derecho de peticion sea mas claro.")
    elif action_key == "accion de cumplimiento":
        if not any(word in full_text for word in ["ley", "decreto", "resolucion", "resolución", "acto administrativo"]):
            blocking_issues.append("La accion de cumplimiento exige identificar la norma o el acto incumplido.")
    elif action_key == "impugnacion de tutela":
        if not any(word in full_text for word in ["fallo", "impugno", "segunda instancia", "error del juez", "decision negada"]):
            blocking_issues.append("La impugnacion necesita identificar el fallo y el desacuerdo juridico concreto.")
    elif action_key == "incidente de desacato":
        if not any(word in full_text for word in ["incumplio", "incumplimiento", "orden judicial", "fallo de tutela"]):
            blocking_issues.append("El desacato requiere identificar la orden judicial incumplida y su incumplimiento.")

    return {
        "rule": rule,
        "status": "requires_more_data" if blocking_issues else "ok_with_warnings" if warnings else "ok",
        "blocking_issues": blocking_issues,
        "warnings": warnings,
    }
