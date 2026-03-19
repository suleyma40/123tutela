from __future__ import annotations

import unicodedata
from typing import Any

from backend.case_architecture import _is_ai_owned_quality_issue
from backend.document_rules import get_document_rule
from backend.legal_sources import validate_document_citations
from backend.quality_llm import score_document_with_claude


QUALITY_PASSING_SCORE = 70
QUALITY_SOFT_CAP = 98


GENERATION_BRIEFS: dict[str, dict[str, Any]] = {
    "accion de tutela": {
        "tone": "firme, tecnico y urgente sin exageraciones",
        "narrative_focus": [
            "cronologia estricta de hechos",
            "conexion entre hecho, derecho fundamental y dano actual",
            "explicar que se intento antes, que dano sigue ocurriendo hoy y si ya existio una tutela previa",
            "orden concreta, medible y ejecutable al juez o accionado",
        ],
        "must_include": [
            "aclarar si ya existio otra tutela previa",
            "explicar que se intento antes o por que el dano requiere intervencion ya",
            "explicar por que el problema sigue siendo actual",
            "pretensiones precisas",
        ],
    },
    "derecho de peticion": {
        "tone": "respetuoso, claro y exigente en respuesta de fondo",
        "narrative_focus": [
            "identificar con precision la entidad destinataria",
            "explicar hechos sin ruido narrativo",
            "formular 2 o 3 soluciones concretas y verificables",
            "mencionar termino legal de respuesta aplicable",
        ],
        "must_include": [
            "soluciones concretas",
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
            "incluir plazo legal de respuesta y advertencia de escalamiento ante Superfinanciera si no hay respuesta de fondo",
        ],
        "must_include": [
            "solicitudes numeradas",
            "producto o cobro identificado",
            "canal de respuesta",
            "termino legal de respuesta",
            "advertencia de escalamiento",
            "fundamento sectorial financiero",
        ],
    },
    "derecho de peticion financiero": {
        "tone": "respetuoso, exigente y orientado a respuesta de fondo",
        "narrative_focus": [
            "identificar claramente el banco o entidad financiera",
            "presentar hechos ordenados cronologicamente",
            "formular soluciones concretas y verificables",
            "mencionar Ley 1755 y termino legal de respuesta",
        ],
        "must_include": ["soluciones concretas", "termino legal", "canal de notificacion"],
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


HEALTH_GENERATION_BRIEFS: dict[str, dict[str, Any]] = {
    "accion de tutela": {
        "tone": "firme, tecnico y clinicamente situado, con urgencia real y sin dramatizacion artificial",
        "narrative_focus": [
            "identificar diagnostico, servicio ordenado, fecha de orden y barrera concreta de la EPS",
            "conectar riesgo actual del paciente con la omision administrativa",
            "explicar procedencia e inmediatez a partir de hechos medicos y soporte cargado",
            "pedir orden judicial especifica, medible y de cumplimiento inmediato",
        ],
        "must_include": [
            "eps o ips accionada",
            "diagnostico o condicion medica",
            "servicio o tratamiento ordenado",
            "barrera concreta de la eps",
            "riesgo actual del paciente",
        ],
    },
    "derecho de peticion": {
        "tone": "respetuoso, clinicamente preciso y exigente en respuesta de fondo",
        "narrative_focus": [
            "identificar eps o ips, diagnostico y servicio de salud requerido",
            "mostrar gestion previa y solicitud concreta de autorizacion o respuesta",
            "pedir respuesta medible y fecha cierta de prestacion del servicio",
        ],
        "must_include": [
            "eps o ips destinataria",
            "servicio de salud requerido",
            "solicitudes claras",
            "termino legal de respuesta",
        ],
    },
    "impugnacion de tutela": {
        "tone": "tecnico, clinico y de contradiccion puntual del fallo",
        "narrative_focus": [
            "identificar el fallo impugnado y el error concreto del juez",
            "resaltar el riesgo medico actual no protegido por la decision",
            "pedir revocatoria o modificacion con orden especifica en salud",
        ],
        "must_include": [
            "fallo impugnado",
            "motivo concreto de desacuerdo",
            "riesgo actual del paciente",
        ],
    },
    "incidente de desacato": {
        "tone": "contundente, probatorio y centrado en incumplimiento de orden de salud",
        "narrative_focus": [
            "identificar fallo, orden medica o servicio incumplido",
            "mostrar que la barrera persiste pese a la orden judicial",
            "pedir cumplimiento inmediato y medidas correctivas",
        ],
        "must_include": [
            "fallo identificado",
            "orden incumplida",
            "incumplimiento actual",
            "afectacion actual en salud",
        ],
    },
}


def get_generation_brief(recommended_action: str | None, workflow_type: str | None = None, category: str | None = None) -> dict[str, Any]:
    rule = get_document_rule(recommended_action, workflow_type)
    action_key = rule["action_key"]
    category_key = _normalize_text(category or "")
    health_override = HEALTH_GENERATION_BRIEFS.get(action_key) if category_key == "salud" else None
    brief = health_override or GENERATION_BRIEFS.get(
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


def _clamp_score(value: int | float, *, ceiling: int = 100) -> int:
    return max(0, min(int(round(value)), ceiling))


def _normalize_text(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value.lower()) if not unicodedata.combining(char)
    )


SECTION_ALIASES: dict[str, list[str]] = {
    "destinatario": ["destinatario", "senores", "doctor", "doctora", "atencion:"],
    "identificacion del consumidor financiero": ["identificacion del consumidor financiero"],
    "identificacion del peticionario": ["identificacion del peticionario"],
    "competencia y reparto": ["competencia y reparto", "i. competencia y reparto"],
    "identificacion del accionante y del accionado": ["identificacion del accionante y del accionado", "ii. identificacion del accionante y del accionado"],
    "derechos fundamentales vulnerados": ["derechos fundamentales vulnerados", "iv. derechos fundamentales vulnerados"],
    "procedencia": ["procedencia", "vi. procedencia"],
    "juramento de no temeridad": ["juramento de no temeridad", "ix. juramento de no temeridad"],
    "hechos y contexto": ["hechos y contexto", "hechos", "hechos relevantes", "ii. hechos"],
    "fundamento del reclamo": ["fundamento del reclamo", "fundamentos de derecho", "fundamento juridico", "iii. fundamentos de derecho"],
    "fundamento del derecho de peticion": ["fundamento del derecho de peticion", "fundamentos de derecho", "iii. fundamentos de derecho"],
    "solicitudes numeradas": ["solicitudes numeradas", "solicitudes concretas", "pretensiones", "v. solicitudes"],
    "pruebas y anexos": ["pruebas y anexos", "anexos", "viii. pruebas y anexos"],
    "anexos y notificaciones": ["anexos y notificaciones", "pruebas y anexos", "notificaciones"],
    "notificaciones": ["notificaciones", "ix. notificaciones"],
    "termino legal de respuesta": ["termino legal de respuesta", "vi. termino legal de respuesta"],
}


def _has_required_section(text: str, section: str) -> bool:
    normalized_text = _normalize_text(text)
    tokens = SECTION_ALIASES.get(_normalize_text(section), [_normalize_text(section)])
    if _contains_any(normalized_text, tokens):
        return True

    normalized_section = _normalize_text(section)
    if normalized_section == "destinatario":
        return _contains_any(
            normalized_text,
            ["nit:", "asunto:", "representante legal", "servicioalcliente@", "defensor@", "telefono:"],
        )
    if normalized_section in {"identificacion del consumidor financiero", "identificacion del peticionario"}:
        return _contains_any(
            normalized_text,
            ["cedula de ciudadania", "persona mayor de edad", "correo electronico", "telefono ", "telefono:"],
        )
    return False


def evaluate_generated_document(case: dict[str, Any], document: str) -> dict[str, Any]:
    recommended_action = case.get("recommended_action")
    workflow_type = case.get("workflow_type")
    category = case.get("categoria") or case.get("category")
    rule = get_document_rule(recommended_action, workflow_type)
    brief = get_generation_brief(recommended_action, workflow_type, category)
    lowered = str(document or "").lower()
    normalized_document = _normalize_text(str(document or ""))
    blocking_issues: list[str] = []
    warnings: list[str] = []
    strengths: list[str] = []
    improvements: list[str] = []

    structure_score = 25
    legal_score = 25
    factual_score = 20
    remedies_score = 20
    operability_score = 10
    source_policy = (case.get("facts") or {}).get("source_validation_policy") or {}
    citation_guard = validate_document_citations(document=document, source_validation_policy=source_policy)

    missing_sections = [section for section in rule["required_sections"] if not _has_required_section(lowered, section)]
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

    if (
        _contains_any(lowered, ["t-", "su-", "c-"])
        and not (source_policy.get("verified_precedents") or [])
        and not (citation_guard.get("verified_detected_references") or [])
    ):
        legal_score -= 10
        warnings.append("La IA debe reforzar o depurar internamente el soporte jurisprudencial antes de entregar el documento final.")
    elif (source_policy.get("verified_sources") or []) and _contains_any(lowered, ["suin-juriscol", "funcion publica", "decreto 2591", "articulo 86", "ley 1755"]):
        strengths.append("El documento se apoya en fuentes juridicas verificadas o conservadoras.")

    if citation_guard.get("has_unverified_citations"):
        legal_score -= 15
        blocking_issues.append(
            "El documento contiene referencias juridicas no verificadas automaticamente: "
            + ", ".join((citation_guard.get("unresolved_detected_references") or [])[:4])
            + "."
        )
        improvements.append("Eliminar o sustituir toda cita no verificada antes de la entrega final.")
    elif citation_guard.get("verified_detected_references"):
        strengths.append("Las referencias juridicas detectadas coinciden con el registro verificable de la app.")

    action_key = rule["action_key"]
    health_block = _normalize_text(category or "") == "salud"
    if action_key == "accion de tutela":
        if not _contains_any(lowered, ["no temeridad", "juramento"]):
            legal_score -= 8
            blocking_issues.append("La tutela no deja claro si ya existio otra tutela por este mismo problema.")
        if not _contains_any(lowered, ["subsidiariedad", "otro medio", "perjuicio irremediable"]):
            legal_score -= 8
            blocking_issues.append("La tutela no explica bien que se intento antes o por que el dano requiere intervencion inmediata.")
        if not _contains_any(lowered, ["inmediatez", "actualmente", "sigue ocurriendo", "reciente"]):
            legal_score -= 4
            warnings.append("La tutela debe explicar mejor que dano o riesgo sigue ocurriendo hoy.")
    elif action_key == "derecho de peticion":
        if not _contains_any(lowered, ["ley 1755", "15 dias", "10 dias", "30 dias"]):
            legal_score -= 6
            warnings.append("El derecho de peticion debe mencionar el termino legal de respuesta.")
        if not _contains_any(lowered, ["1.", "2.", "1)", "2)", "solicitudes"]):
            remedies_score -= 8
            blocking_issues.append("El derecho de peticion necesita dejar mas claras las respuestas o soluciones concretas que esperas recibir.")
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

    if health_block:
        if action_key in {"accion de tutela", "derecho de peticion", "impugnacion de tutela", "incidente de desacato"}:
            if not _contains_any(normalized_document, ["eps", "ips", "entidad accionada", "nueva eps", "sura", "sanitas"]):
                factual_score -= 6
                blocking_issues.append("El documento de salud debe identificar claramente la EPS o IPS responsable.")
            if not _contains_any(normalized_document, ["diagnostico", "condicion medica", "condicion de salud", "patologia", "enfermedad"]):
                factual_score -= 6
                warnings.append("Conviene hacer mas visible el diagnostico o condicion medica principal.")
            if not _contains_any(normalized_document, ["medicamento", "examen", "procedimiento", "servicio de salud", "tratamiento", "autorizacion"]):
                factual_score -= 6
                blocking_issues.append("El documento de salud debe individualizar el servicio, examen, medicamento o tratamiento requerido.")
            if not _contains_any(normalized_document, ["riesgo", "agravamiento", "deterioro", "afectacion actual", "vida digna", "salud"]):
                legal_score -= 4
                warnings.append("Conviene reforzar el riesgo actual del paciente para darle mayor fuerza al documento de salud.")
        if action_key == "accion de tutela":
            if not _contains_any(normalized_document, ["ley estatutaria 1751", "ley 1751", "articulo 49", "articulo 86", "decreto 2591"]):
                legal_score -= 8
                blocking_issues.append("La tutela en salud debe apoyarse al menos en el articulo 49, el articulo 86, la Ley 1751 o el Decreto 2591.")
            if not _contains_any(normalized_document, ["nego", "negó", "silencio", "no autoriz", "demoro", "barrera", "omision"]):
                factual_score -= 4
                warnings.append("La tutela en salud debe describir con mayor precision la barrera concreta de la EPS.")
        elif action_key == "derecho de peticion":
            if not _contains_any(normalized_document, ["ley 1755", "termino legal", "respuesta de fondo"]):
                legal_score -= 4
                warnings.append("El derecho de peticion en salud debe dejar mas visible la obligacion de respuesta de fondo.")
        elif action_key == "impugnacion de tutela":
            if not _contains_any(normalized_document, ["fallo", "impugnacion", "segunda instancia", "revocar", "modificar"]):
                legal_score -= 6
                blocking_issues.append("La impugnacion de salud debe identificar mejor el fallo y la solicitud a segunda instancia.")
        elif action_key == "incidente de desacato":
            if not _contains_any(normalized_document, ["desacato", "incumplimiento", "orden judicial", "cumplimiento inmediato"]):
                legal_score -= 6
                blocking_issues.append("El desacato en salud debe mostrar la orden judicial incumplida y pedir cumplimiento inmediato.")

    total_score = max(0, structure_score + legal_score + factual_score + remedies_score + operability_score)
    llm_qa = score_document_with_claude(
        case=case,
        document=document,
        base_review={
            "score": total_score,
            "blocking_issues": blocking_issues,
            "warnings": warnings,
            "strengths": strengths,
            "improvements": improvements,
        },
    )
    if llm_qa:
        adjusted_score = int(llm_qa.get("adjusted_score") or total_score)
        llm_blocking = list(llm_qa.get("blocking_issues") or [])
        ai_owned_llm_blocking = [issue for issue in llm_blocking if _is_ai_owned_quality_issue(issue)]
        actionable_llm_blocking = [issue for issue in llm_blocking if not _is_ai_owned_quality_issue(issue)]
        if blocking_issues or actionable_llm_blocking:
            total_score = min(total_score, adjusted_score)
        else:
            # When the document is already structurally sound and the LLM only has
            # calibration feedback, blend both signals instead of letting the
            # probabilistic review hard-cap a near-production document.
            blended_score = (total_score * 0.7) + (adjusted_score * 0.3)
            total_score = _clamp_score(blended_score, ceiling=QUALITY_SOFT_CAP)
        blocking_issues = list(dict.fromkeys([*blocking_issues, *actionable_llm_blocking]))
        warnings = list(
            dict.fromkeys(
                [
                    *warnings,
                    *(llm_qa.get("warnings") or []),
                    *ai_owned_llm_blocking,
                ]
            )
        )
        strengths = list(dict.fromkeys([*strengths, *(llm_qa.get("strengths") or [])]))
        improvements = list(dict.fromkeys([*improvements, *(llm_qa.get("improvements") or [])]))
        if ai_owned_llm_blocking:
            improvements.append("La IA debe reforzar internamente el soporte juridico verificable antes de la entrega final.")
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
        "llm_qa": llm_qa or {},
        "citation_guard": citation_guard,
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
