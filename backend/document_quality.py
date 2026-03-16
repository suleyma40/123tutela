from __future__ import annotations

from typing import Any

from backend.document_rules import get_document_rule


QUALITY_PASSING_SCORE = 70


GENERATION_BRIEFS: dict[str, dict[str, Any]] = {
    "accion de tutela": {
        "tone": "firme, tecnico y urgente sin exageraciones",
        "narrative_focus": [
            "cronologia estricta de hechos",
            "conexion entre hecho, derecho fundamental y dano actual",
            "procedencia por subsidiariedad, inmediatez y no temeridad",
            "orden concreta, medible y ejecutable al juez o accionado",
        ],
        "must_include": [
            "juramento de no temeridad",
            "subsidiariedad o perjuicio irremediable",
            "explicacion de inmediatez",
            "pretensiones precisas",
        ],
    },
    "derecho de peticion": {
        "tone": "respetuoso, claro y exigente en respuesta de fondo",
        "narrative_focus": [
            "identificar con precision la entidad destinataria",
            "explicar hechos sin ruido narrativo",
            "formular solicitudes numeradas y verificables",
            "mencionar termino legal de respuesta aplicable",
        ],
        "must_include": [
            "solicitudes numeradas",
            "canal de notificacion",
            "termino legal o Ley 1755",
        ],
    },
    "queja formal": {
        "tone": "serio, institucional y verificable",
        "narrative_focus": [
            "conducta irregular o mal servicio claramente descrito",
            "impacto concreto para el usuario",
            "respuesta institucional esperada",
        ],
        "must_include": ["hechos verificables", "solicitud de intervencion"],
    },
    "reclamo administrativo": {
        "tone": "tecnico, directo y orientado a correccion",
        "narrative_focus": [
            "acto, cobro o decision cuestionada",
            "razon juridica o factica del reclamo",
            "correccion concreta solicitada",
        ],
        "must_include": ["acto o cobro identificado", "solucion concreta"],
    },
    "reclamacion financiera": {
        "tone": "firme, claro y tecnico como consumidor financiero",
        "narrative_focus": [
            "identificar producto, cobro o seguro cuestionado",
            "explicar por que el cargo no fue autorizado o no fue informado",
            "pedir devolucion, reverso o cancelacion con respuesta formal",
        ],
        "must_include": ["solicitudes numeradas", "producto o cobro identificado", "canal de respuesta"],
    },
    "derecho de peticion financiero": {
        "tone": "respetuoso, exigente y orientado a respuesta de fondo",
        "narrative_focus": [
            "identificar claramente el banco o entidad financiera",
            "presentar hechos ordenados cronologicamente",
            "formular solicitudes numeradas y verificables",
            "mencionar Ley 1755 y termino legal de respuesta",
        ],
        "must_include": ["solicitudes numeradas", "termino legal", "canal de notificacion"],
    },
    "queja disciplinaria": {
        "tone": "sobrio, serio y centrado en hechos atribuibles",
        "narrative_focus": [
            "identificar funcionario o rol",
            "describir conducta disciplinariamente relevante",
            "pedir actuacion investigativa seria",
        ],
        "must_include": ["sujeto disciplinable", "fecha o periodo del hecho"],
    },
    "accion de cumplimiento": {
        "tone": "tecnico y centrado en deber exigible",
        "narrative_focus": [
            "norma o acto claro",
            "autoridad obligada",
            "renuencia o incumplimiento actual",
        ],
        "must_include": ["norma o acto incumplido", "requerimiento previo"],
    },
    "impugnacion de tutela": {
        "tone": "tecnico y de contradiccion argumentativa",
        "narrative_focus": [
            "identificar fallo y termino",
            "responder razones concretas del juez",
            "pedir revocatoria o modificacion precisa",
        ],
        "must_include": ["fallo impugnado", "contraargumento concreto", "termino"],
    },
    "incidente de desacato": {
        "tone": "contundente y probatorio",
        "narrative_focus": [
            "identificar fallo y orden judicial",
            "probar notificacion",
            "describir incumplimiento actual",
        ],
        "must_include": ["fallo identificado", "notificacion", "orden incumplida"],
    },
    "carta formal a entidad": {
        "tone": "claro, firme y profesional",
        "narrative_focus": [
            "hechos resumidos y concretos",
            "solicitud puntual",
            "canal claro de respuesta",
        ],
        "must_include": ["destinatario", "solicitud concreta"],
    },
}


def get_generation_brief(recommended_action: str | None, workflow_type: str | None = None) -> dict[str, Any]:
    rule = get_document_rule(recommended_action, workflow_type)
    action_key = rule["action_key"]
    brief = GENERATION_BRIEFS.get(
        action_key,
        {
            "tone": "claro, serio y accionable",
            "narrative_focus": [
                "hechos verificables",
                "fundamento juridico suficiente",
                "pretensiones concretas y medibles",
            ],
            "must_include": ["hechos", "pretensiones", "notificaciones"],
        },
    )
    return {
        "action_key": action_key,
        "document_title": rule["document_title"],
        "goal": rule["goal"],
        "tone": brief["tone"],
        "narrative_focus": brief["narrative_focus"],
        "must_include": brief["must_include"],
        "required_sections": rule["required_sections"],
        "quality_focus": rule["quality_focus"],
    }


def _contains_any(text: str, tokens: list[str]) -> bool:
    return any(token in text for token in tokens)


def evaluate_generated_document(case: dict[str, Any], document: str) -> dict[str, Any]:
    recommended_action = case.get("recommended_action")
    workflow_type = case.get("workflow_type")
    rule = get_document_rule(recommended_action, workflow_type)
    brief = get_generation_brief(recommended_action, workflow_type)
    lowered = str(document or "").lower()
    blocking_issues: list[str] = []
    warnings: list[str] = []
    strengths: list[str] = []
    improvements: list[str] = []

    structure_score = 25
    legal_score = 25
    factual_score = 20
    remedies_score = 20
    operability_score = 10

    missing_sections = [section for section in rule["required_sections"] if section.lower() not in lowered]
    if missing_sections:
        penalty = min(15, len(missing_sections) * 3)
        structure_score -= penalty
        warnings.append("Faltan secciones esperadas: " + ", ".join(missing_sections[:4]) + ".")
        improvements.append("Completar todas las secciones obligatorias del tipo de documento.")
    else:
        strengths.append("La estructura base del documento cubre las secciones criticas esperadas.")

    if len(document.split()) < 220:
        factual_score -= 10
        warnings.append("El documento sigue corto para sostener una argumentacion juridica robusta.")
        improvements.append("Ampliar hechos y contexto con cronologia y afectacion concreta.")
    else:
        strengths.append("La longitud del borrador permite una sustentacion inicial suficiente.")

    if not _contains_any(lowered, ["hechos", "cronologia", "problema central", "hechos relevantes"]):
        factual_score -= 5
        improvements.append("Hacer mas visible la cronologia o el bloque de hechos relevantes.")

    if not _contains_any(lowered, ["constitucion", "ley", "decreto", "art.", "articulo"]):
        legal_score -= 10
        warnings.append("El documento casi no muestra anclaje normativo explicito.")
        improvements.append("Agregar fundamento normativo verificable y pertinente.")
    else:
        strengths.append("El borrador incluye anclaje normativo minimo.")

    if not _contains_any(lowered, ["solicito", "pretensiones", "ordene", "ordenen", "requiero", "peticiones"]):
        remedies_score -= 12
        blocking_issues.append("El documento no deja suficientemente claras las pretensiones u ordenes solicitadas.")
        improvements.append("Expresar pretensiones numeradas, medibles y ejecutables.")
    else:
        strengths.append("El documento formula solicitudes o pretensiones identificables.")

    if not _contains_any(lowered, ["notificaciones", "correo", "telefono"]):
        operability_score -= 4
        warnings.append("Conviene reforzar el bloque de notificaciones del accionante.")

    action_key = rule["action_key"]
    if action_key == "accion de tutela":
        if not _contains_any(lowered, ["no temeridad", "juramento"]):
            legal_score -= 8
            blocking_issues.append("La tutela no contiene juramento o declaracion de no temeridad.")
        if not _contains_any(lowered, ["subsidiariedad", "otro medio", "perjuicio irremediable"]):
            legal_score -= 8
            blocking_issues.append("La tutela no justifica subsidiariedad ni perjuicio irremediable.")
        if not _contains_any(lowered, ["inmediatez", "actualmente", "sigue ocurriendo", "reciente"]):
            legal_score -= 4
            warnings.append("La tutela debe reforzar la inmediatez del dano o la vulneracion.")
    elif action_key == "derecho de peticion":
        if not _contains_any(lowered, ["ley 1755", "15 dias", "10 dias", "30 dias"]):
            legal_score -= 6
            warnings.append("El derecho de peticion debe mencionar el termino legal de respuesta.")
        if not _contains_any(lowered, ["1.", "2.", "1)", "2)", "solicitudes"]):
            remedies_score -= 8
            blocking_issues.append("El derecho de peticion necesita solicitudes numeradas mas claras.")
    elif action_key == "impugnacion de tutela":
        if not _contains_any(lowered, ["3 dias", "notificacion", "fallo impugnado"]):
            legal_score -= 8
            blocking_issues.append("La impugnacion no deja claro el termino o el fallo cuestionado.")
        if not _contains_any(lowered, ["error del juez", "valoracion", "desacuerdo"]):
            legal_score -= 6
            warnings.append("La impugnacion debe contraargumentar mejor el razonamiento del fallo.")
    elif action_key == "incidente de desacato":
        if not _contains_any(lowered, ["notificado", "notificacion"]):
            legal_score -= 8
            blocking_issues.append("El desacato no deja clara la notificacion del fallo.")
        if not _contains_any(lowered, ["incumplimiento", "orden incumplida", "fallo de tutela"]):
            legal_score -= 8
            blocking_issues.append("El desacato no describe con precision el incumplimiento actual.")

    total_score = max(0, structure_score + legal_score + factual_score + remedies_score + operability_score)
    passed = total_score >= QUALITY_PASSING_SCORE and not blocking_issues

    if passed:
        strengths.append("El borrador supera el umbral minimo de calidad juridica automatica.")
    else:
        improvements.append("No entregar silenciosamente; pedir mas datos o regenerar el documento.")

    return {
        "score": total_score,
        "passed": passed,
        "threshold": QUALITY_PASSING_SCORE,
        "rule": rule,
        "brief": brief,
        "dimension_scores": {
            "structure": structure_score,
            "legal_strength": legal_score,
            "factual_clarity": factual_score,
            "remedy_specificity": remedies_score,
            "operability": operability_score,
        },
        "blocking_issues": list(dict.fromkeys(blocking_issues)),
        "warnings": list(dict.fromkeys(warnings)),
        "strengths": list(dict.fromkeys(strengths)),
        "suggested_improvements": list(dict.fromkeys(improvements)),
    }
