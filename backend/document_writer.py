from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
import unicodedata

from backend.agent_registry import resolve_health_document
from backend.document_rules import get_document_rule


def _join_list(value: Any, fallback: str = "No informado") -> str:
    if isinstance(value, list):
        clean = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(clean) if clean else fallback
    text = str(value or "").strip()
    return text or fallback


def _numbered_lines(items: list[str]) -> str:
    items = [str(item).strip() for item in items if str(item).strip()]
    if not items:
        return "1. Sin informacion adicional registrada."
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def _split_numbered_requests(value: str | None) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    parts = re.split(r"(?:^|\s)(?:\d+[\.\)])\s*", text)
    clean = [_sentence(_title_sentence(item.strip()), fallback="").strip() for item in parts if item.strip()]
    return [item for item in clean if item]


def _paragraph_lines(items: list[str], fallback: str = "Sin informacion adicional registrada.") -> str:
    items = [str(item).strip() for item in items if str(item).strip()]
    if not items:
        return fallback
    return "\n\n".join(items)


def _section(title: str, body: str) -> str:
    return f"{title}\n{body.strip()}\n"


def _sentence(value: str | None, fallback: str = "No informado.") -> str:
    text = str(value or "").strip()
    if not text:
        return fallback
    if text[-1] not in ".;:":
        text += "."
    return text


def _normalize_writer_text(value: str) -> str:
    text = str(value or "")
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def _title_sentence(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text[:1].upper() + text[1:]


def _list_from_insights(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _dedupe_lines(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = " ".join(str(item or "").strip().lower().split())
        if not text or text in seen:
            continue
        seen.add(text)
        deduped.append(str(item).strip())
    return deduped


def _looks_like_internal_evidence_label(text: str) -> bool:
    lowered = str(text or "").strip().lower()
    return lowered.startswith("soporte relacionado con ")


def _clean_financial_evidence_items(base_items: list[str], suggested: list[str], *, has_prior_claim: bool) -> list[str]:
    normalized_map = {
        "extractos": "Extractos, estados de cuenta o movimientos donde consten los cobros controvertidos.",
        "extractos pdf": "Extractos, estados de cuenta o movimientos donde consten los cobros controvertidos.",
        "pantallazos": "Capturas o pantallazos donde se evidencien los cobros cuestionados.",
        "capturas": "Capturas o pantallazos donde se evidencien los cobros cuestionados.",
        "contrato": "Contrato, reglamento, certificado o soporte del producto financiero asociado.",
        "chat o correo": "Chats, correos o comunicaciones con la entidad sobre el cobro reclamado.",
        "correos": "Chats, correos o comunicaciones con la entidad sobre el cobro reclamado.",
        "radicado previo": "Constancia de radicado o respuesta previa de la entidad financiera." if has_prior_claim else "",
        "documentos soporte": "Documentos soporte relacionados con el cobro reclamado.",
    }
    items = list(base_items)
    for evidence in suggested:
        key = str(evidence or "").strip().lower()
        mapped = normalized_map.get(key, "")
        if mapped:
            items.append(mapped)
    deduped: list[str] = []
    seen_groups: set[str] = set()
    for item in _dedupe_lines(items):
        lowered = item.lower()
        if "extract" in lowered or "estado de cuenta" in lowered or "movimiento" in lowered:
            group = "extractos"
        elif "captura" in lowered or "pantallazo" in lowered:
            group = "capturas"
        elif "chat" in lowered or "correo" in lowered or "comunicacion" in lowered:
            group = "comunicaciones"
        elif "contrato" in lowered or "reglamento" in lowered or "certificado" in lowered or "constancia" in lowered:
            group = "contrato"
        elif "radicado" in lowered or "respuesta previa" in lowered:
            group = "radicado"
        else:
            group = lowered
        if group in seen_groups:
            continue
        seen_groups.add(group)
        deduped.append(item)
    return deduped


def _detect_refund_destination(intake: dict[str, Any], case: dict[str, Any]) -> str:
    direct = str(intake.get("refund_destination") or "").strip()
    if direct:
        lowered = direct.lower()
        reference = re.sub(r"[^\d]", "", str(intake.get("bank_account_reference") or ""))
        if "misma tarjeta" in lowered or direct.lower() == "tarjeta":
            if len(reference) >= 4:
                return f"la misma tarjeta terminada en {reference[-4:]}"
            return "la misma tarjeta donde se facturaron los cobros"
        if "misma cuenta" in lowered:
            return "la misma cuenta asociada al producto financiero"
        return direct
    text = " ".join(
        str(part).strip().lower()
        for part in [
            intake.get("concrete_request"),
            intake.get("case_story"),
            case.get("descripcion"),
            (case.get("facts") or {}).get("hechos_principales"),
        ]
        if str(part or "").strip()
    )
    if "misma tarjeta" in text or "a la tarjeta" in text or "a mi tarjeta" in text:
        reference = str(intake.get("bank_account_reference") or "").strip()
        if reference:
            return f"la misma tarjeta terminada en {reference}"
        return "la misma tarjeta donde se facturaron los cobros"
    if "misma cuenta" in text or "a mi cuenta" in text or "a la cuenta" in text:
        return "la misma cuenta asociada al producto financiero"
    return ""


def _parse_cop_amount(value: str) -> int | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return None
    try:
        return int(digits)
    except Exception:
        return None


def _format_cop_amount(value: int | None) -> str:
    if value is None:
        return ""
    return f"${value:,}".replace(",", ".")


def _amount_looks_approximate(value: str) -> bool:
    lowered = str(value or "").strip().lower()
    if not lowered:
        return True
    return any(
        token in lowered
        for token in [
            "aproxim",
            "estimad",
            "mas o menos",
            "cerca de",
            "alrededor",
            "sin perjuicio",
        ]
    )


def _normalize_account_reference(reference: str) -> str:
    text = str(reference or "").strip()
    if not text:
        return ""
    digits = re.sub(r"[^\d]", "", text)
    if len(digits) >= 4:
        return f"tarjeta terminada en {digits[-4:]}"
    return text


def _person_name(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return "Usuario"
    if text == text.lower():
        return " ".join(part.capitalize() for part in text.split())
    return text


def _clean_health_person_name(value: str | None) -> str:
    text = str(value or "").strip(" .,:;")
    if not text:
        return ""
    lowered = _normalize_writer_text(text)
    banned = (
        "atencion",
        "plan",
        "historia clinica",
        "medicamento",
        "formula",
        "ips",
        "eps",
        "aneurisma",
        "consulta",
        "servicio",
    )
    if any(fragment in lowered for fragment in banned):
        return ""
    tokens = re.findall(r"[A-Za-z]{2,}", unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii"))
    if len(tokens) < 2:
        return ""
    return _person_name(" ".join(tokens[:4]))


def _normalize_health_service_text(value: str | None) -> str:
    text = str(value or "").strip(" .,:;")
    if not text:
        return ""
    normalized = _normalize_writer_text(text)
    replacements = {
        "moujarou": "mounjaro",
        "moujaro": "mounjaro",
        "emdicamento": "medicamento",
    }
    for wrong, right in replacements.items():
        normalized = normalized.replace(wrong, right)
    normalized = re.sub(r"^el\s+", "", normalized).strip()
    if not normalized:
        return ""
    words = normalized.split()
    if len(words) <= 3:
        return " ".join(word.capitalize() for word in words)
    return normalized[:1].upper() + normalized[1:]


def _health_attachment_suggestions(case: dict[str, Any]) -> dict[str, Any]:
    facts = case.get("facts") or {}
    return ((facts.get("attachment_intelligence") or {}).get("typed_suggestions") or {})


def _same_identity(name_a: str, name_b: str, doc_a: str, doc_b: str) -> bool:
    normalized_a = _normalize_writer_text(name_a)
    normalized_b = _normalize_writer_text(name_b)
    digits_a = re.sub(r"\D", "", str(doc_a or ""))
    digits_b = re.sub(r"\D", "", str(doc_b or ""))
    if digits_a and digits_b:
        return digits_a == digits_b
    return bool(normalized_a and normalized_b and normalized_a == normalized_b)


def _titleish_place(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text == text.lower():
        return " ".join(part.capitalize() for part in text.split())
    return text


def _normalize_health_display_date(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    normalized = {
        "dicciembre": "diciembre",
        "setiembre": "septiembre",
    }
    for wrong, right in normalized.items():
        text = re.sub(rf"(?i)\b{wrong}\b", right, text)
    return text


def _clean_uploaded_file_label(name: str) -> str:
    text = str(name or "").strip()
    if not text:
        return ""
    text = re.sub(r"\s*\(\d+\)(?=\.[A-Za-z0-9]+$)", "", text)
    text = re.sub(r"[_]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _financial_amount_breakdown(case: dict[str, Any], intake: dict[str, Any]) -> dict[str, Any]:
    facts = case.get("facts") or {}
    attachment_intelligence = facts.get("attachment_intelligence") or {}
    profiles = attachment_intelligence.get("attachment_profiles") or []
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for profile in profiles:
        if str(profile.get("type") or "").strip() != "extracto":
            continue
        suggestions = profile.get("suggestions") or {}
        date = str(suggestions.get("bank_event_date") or "").strip()
        amount_text = str(suggestions.get("bank_amount_involved") or "").strip()
        parsed = _parse_cop_amount(amount_text)
        if not date or parsed is None:
            continue
        key = (date.lower(), str(parsed))
        if key in seen:
            continue
        seen.add(key)
        entries.append({"date": date, "amount": parsed, "amount_text": _format_cop_amount(parsed)})

    total = sum(item["amount"] for item in entries) if entries else None
    raw_amount = str(intake.get("bank_amount_involved") or "").strip()
    parsed_raw = _parse_cop_amount(raw_amount)
    event_label = str(intake.get("bank_event_date") or intake.get("key_dates") or "").strip()
    inferred_month_count: int | None = None
    inferred_total: int | None = None
    start_month = _month_year_from_label(event_label)
    if not entries and parsed_raw is not None and start_month:
        now = datetime.now()
        months = (now.year - start_month[0]) * 12 + (now.month - start_month[1]) + 1
        if months > 0:
            inferred_month_count = months
            inferred_total = parsed_raw * months
    exact_known = bool(entries) or (bool(raw_amount) and not _amount_looks_approximate(raw_amount) and parsed_raw is not None)
    return {
        "entries": entries,
        "total": total,
        "raw_amount": raw_amount,
        "parsed_raw": parsed_raw,
        "exact_total_text": _format_cop_amount(total if total is not None else parsed_raw),
        "inferred_month_count": inferred_month_count,
        "inferred_total": inferred_total,
        "inferred_total_text": _format_cop_amount(inferred_total),
        "event_label": event_label,
        "exact_known": exact_known,
    }


def _uploaded_evidence_items(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    uploaded_files = facts.get("uploaded_evidence_files") or []
    items = ["Copia del documento de identidad de la persona firmante."]
    evidence_summary = str(intake.get("evidence_summary") or intake.get("supporting_documents") or "").strip()
    if evidence_summary:
        items.append(f"Soportes reportados por la persona usuaria: {_sentence(evidence_summary)}")
    medical_order_date = str(intake.get("medical_order_date") or "").strip()
    treating_doctor_name = str(intake.get("treating_doctor_name") or "").strip()
    if medical_order_date or treating_doctor_name:
        doctor_fragment = f" suscrita por {treating_doctor_name}" if treating_doctor_name else ""
        date_fragment = f" de fecha {medical_order_date}" if medical_order_date else ""
        items.append(f"Orden o formula medica{doctor_fragment}{date_fragment}.")
    if str(intake.get("tutela_court_name") or "").strip():
        court_name = str(intake.get("tutela_court_name") or "").strip()
        ruling_date = str(intake.get("tutela_ruling_date") or "").strip()
        date_fragment = f" de fecha {ruling_date}" if ruling_date else ""
        items.append(f"Copia del fallo de tutela proferido por {court_name}{date_fragment}.")
    if str(intake.get("tutela_order_summary") or "").strip():
        items.append(f"Constancia de la orden judicial cuyo cumplimiento se exige: {_sentence(str(intake.get('tutela_order_summary') or '').strip())}")
    if str(intake.get("tutela_noncompliance_detail") or "").strip():
        items.append("Soportes del incumplimiento actual del fallo de tutela o de la persistencia de la barrera en salud.")
    for file_info in uploaded_files:
        name = _clean_uploaded_file_label(str((file_info or {}).get("original_name") or "").strip())
        if name:
            items.append(f"Documento aportado: {name}.")
    return _dedupe_lines(items)


def _extract_month_reference(text: str) -> str:
    lowered = str(text or "").lower()
    months = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    for month in months:
        if month in lowered:
            year_match = __import__("re").search(r"(20\d{2})", lowered)
            if year_match:
                return f"{month} de {year_match.group(1)}"
            return f"{month} del periodo reportado"
    relative_match = __import__("re").search(r"hace\s+\d+\s+(?:mes|meses|semana|semanas|dia|dias)", lowered)
    if relative_match:
        return relative_match.group(0)
    return ""


def _month_year_from_label(text: str) -> tuple[int, int] | None:
    lowered = str(text or "").strip().lower()
    months = {
        "enero": 1,
        "febrero": 2,
        "marzo": 3,
        "abril": 4,
        "mayo": 5,
        "junio": 6,
        "julio": 7,
        "agosto": 8,
        "septiembre": 9,
        "octubre": 10,
        "noviembre": 11,
        "diciembre": 12,
    }
    for label, month in months.items():
        if label in lowered:
            year_match = re.search(r"(20\d{2})", lowered)
            if year_match:
                return (int(year_match.group(1)), month)
    return None


def _financial_date_label(intake: dict[str, Any], facts: dict[str, Any], description: str) -> str:
    direct = str(intake.get("bank_event_date") or intake.get("key_dates") or "").strip()
    if direct and "no se mencionan" not in direct.lower():
        return direct
    for candidate in [
        str(facts.get("fechas_mencionadas") or "").strip(),
        str(facts.get("hechos_principales") or "").strip(),
        str(description or "").strip(),
    ]:
        label = _extract_month_reference(candidate)
        if label:
            return label
    return "una fecha aproximada que debe precisarse con el extracto o la certificacion bancaria"


def _source_index_by_type(sources: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {"norma": [], "jurisprudencia": [], "guia_institucional": []}
    for source in sources:
        source_type = str(source.get("tipo_fuente") or "").strip()
        if source_type in index:
            index[source_type].append(source)
    return index


def _financial_case_flags(case: dict[str, Any]) -> dict[str, bool]:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    combined = " ".join(
        str(item or "")
        for item in [
            case.get("descripcion"),
            facts.get("hechos_principales"),
            intake.get("disputed_charge"),
            intake.get("concrete_request"),
        ]
    ).lower()
    has_report_issue = any(token in combined for token in ["datacredito", "data credito", "transunion", "central de riesgo", "reporte negativo", "reporte"])
    has_data_issue = has_report_issue or any(token in combined for token in ["habeas data", "datos personales", "tratamiento de datos"])
    return {"has_report_issue": has_report_issue, "has_data_issue": has_data_issue}


def _financial_constitutional_basis_text(constitutional_sources: list[dict[str, Any]], *, has_data_issue: bool) -> str:
    explanations: list[str] = []
    for source in constitutional_sources:
        ref = str(source.get("numero_sentencia_o_norma") or "").strip()
        article = ref.replace("Articulo", "Artículo")
        if "13" in ref:
            explanations.append(f"{article} de la Constitución Política: protege a la consumidora frente a tratos arbitrarios y prácticas abusivas en una relación claramente asimétrica.")
        elif "15" in ref:
            explanations.append(f"{article} de la Constitución Política: ampara el habeas data y exige autorización válida para usar información financiera o vincular productos no solicitados.")
        elif "23" in ref:
            explanations.append(f"{article} de la Constitución Política: garantiza una respuesta pronta, completa y de fondo frente a la reclamación presentada.")
        elif "78" in ref:
            explanations.append(f"{article} de la Constitución Política: impone la protección constitucional del consumidor y el deber de información clara, suficiente y verificable.")
    return "\n".join(f"- {line}" for line in explanations if line) or "- La reclamación se sustenta en la protección constitucional del consumidor y en el derecho a obtener respuesta de fondo."


def _financial_legal_basis_text(legal_sources: list[dict[str, Any]], *, has_data_issue: bool, has_report_issue: bool) -> str:
    if not legal_sources:
        return "- El caso exige revisar el régimen especial del consumidor financiero y la normativa general de protección al consumidor."
    wanted = {
        "Ley 1328 de 2009": "Marco principal del consumidor financiero. Refuerza los deberes de información, atención, reclamación y prohibición de prácticas abusivas.",
        "Ley 1480 de 2011": "Complementa la protección frente a información insuficiente, cobros no consentidos y prácticas abusivas.",
        "Ley 1755 de 2015": "Fija el deber de responder de fondo dentro del término legal cuando el usuario presenta una reclamación formal.",
        "Decreto 2555 de 2010": "Compila la regulación del sector financiero y refuerza los deberes de diligencia, transparencia y soporte del producto cobrado.",
        "Circular Externa 029 de 2014": "Contiene instrucciones de la Superintendencia Financiera sobre protección del consumidor financiero y deberes de información.",
        "Ley 1266 de 2008": "Aplica cuando el cobro impacta reportes o historiales crediticios y permite exigir su corrección en centrales de riesgo.",
        "Ley 1581 de 2012": "Refuerza la exigencia de autorización previa, expresa e informada para el tratamiento de datos personales.",
    }
    preferred_order = [
        "Ley 1328 de 2009",
        "Ley 1480 de 2011",
        "Ley 1755 de 2015",
        "Decreto 2555 de 2010",
        "Circular Externa 029 de 2014",
        "Ley 1266 de 2008",
        "Ley 1581 de 2012",
    ]
    available: set[str] = set()
    for source in legal_sources:
        ref = str(source.get("numero_sentencia_o_norma") or "").strip()
        for prefix in wanted:
            if ref.startswith(prefix):
                available.add(prefix)
    lines = [f"- {prefix}: {wanted[prefix]}" for prefix in preferred_order if prefix in available]
    return "\n".join(lines) or "- El caso se apoya en normas verificadas del régimen del consumidor financiero, protección al consumidor y derecho de petición."


def _financial_jurisprudence_text(precedents: list[dict[str, Any]]) -> str:
    if not precedents:
        return "No se incluyeron sentencias específicas porque el sistema no encontró soporte jurisprudencial verificable suficiente para este punto y prefirió conservar un fundamento normativo seguro."
    known = {
        "Sentencia T-302 de 2020": "La Corte examinó la gestión bancaria de pólizas asociadas a productos financieros y reiteró el deber de información clara, completa y oportuna frente a la persona usuaria.",
        "Sentencia T-676 de 2016": "La Corte precisó que las entidades financieras y aseguradoras no pueden desinformar al usuario ni frustrar la posibilidad real de reclamar la póliza o corregir el cobro asociado.",
    }
    lines: list[str] = []
    used: set[str] = set()
    for precedent in precedents:
        ref = str(precedent.get("numero_sentencia_o_norma") or "").strip()
        if ref in known and ref not in used:
            lines.append(f"- {ref} ({precedent.get('corporacion')}): {known[ref]}")
            used.add(ref)
    return "\n".join(lines) or "La reclamación se mantuvo en un nivel normativo conservador porque no se validaron precedentes adicionales con trazabilidad suficiente."


def _generic_facts(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    chronology = _list_from_insights(insights.get("chronology"))
    if chronology:
        return chronology

    lines: list[str] = []
    main_facts = str(facts.get("hechos_principales") or case.get("descripcion") or "").strip()
    if main_facts:
        lines.append(_sentence(main_facts))
    entities = _join_list(facts.get("entidades_involucradas"), fallback="")
    if entities:
        lines.append(f"Se identifica como entidad o destinatario involucrado a {entities}.")
    dates = _join_list(facts.get("fechas_mencionadas"), fallback="")
    if dates:
        lines.append(f"Las referencias temporales relevantes del caso son las siguientes: {dates}.")
    central_problem = str(facts.get("problema_central") or "").strip()
    if central_problem:
        lines.append(f"El problema central del caso puede sintetizarse asi: {central_problem}.")
    return lines or ["La persona usuaria reporta una situacion que requiere documentacion juridica y seguimiento formal."]


def _generic_failures(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    failures = _list_from_insights(insights.get("entity_failures"))
    if failures:
        return failures
    return ["Se advierte una actuacion presuntamente irregular de la entidad o autoridad involucrada que exige respuesta de fondo y correccion efectiva."]


def _generic_pretensions(case: dict[str, Any], action_key: str) -> list[str]:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    pretensions = _list_from_insights(insights.get("pretensions"))
    if pretensions:
        return pretensions

    intake_form = facts.get("intake_form") or {}
    concrete_request = str(intake_form.get("concrete_request") or facts.get("pretension_concreta") or "").strip()
    if concrete_request:
        return [concrete_request, "Que la entidad emita respuesta formal y verificable frente a cada solicitud planteada."]

    description = str(case.get("descripcion") or "").lower()
    if action_key == "accion de tutela":
        return [
            "Que se amparen de manera inmediata los derechos fundamentales comprometidos.",
            "Que se ordene a la entidad accionada la actuacion concreta necesaria para cesar la vulneracion.",
        ]
    if action_key in {"derecho de peticion", "derecho de peticion financiero"}:
        return [
            "Que se emita respuesta de fondo, clara, congruente y completa frente a este escrito.",
            "Que se remita respuesta por el canal de notificacion informado por la persona usuaria.",
        ]
    if "solicito" in description or "requiero" in description:
        return ["Que se atienda de fondo la solicitud planteada por la persona usuaria."]
    return ["Que se adopte la medida correctiva o de proteccion que corresponda conforme a los hechos narrados."]


def _health_context(case: dict[str, Any]) -> dict[str, Any]:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}
    document_profile = resolve_health_document(
        workflow_type=case.get("workflow_type"),
        recommended_action=case.get("recommended_action"),
    )
    accionado = str(intake.get("target_entity") or primary.get("name") or _join_list(facts.get("entidades_involucradas"), fallback="Entidad accionada")).strip()
    return {
        "facts": facts,
        "intake": intake,
        "legal_analysis": legal_analysis,
        "routing": routing,
        "primary": primary,
        "document_profile": document_profile,
        "accionado": accionado,
        "user_name": _person_name(case.get("usuario_nombre") or intake.get("full_name")),
        "user_doc": case.get("usuario_documento") or intake.get("document_number") or "Sin documento registrado",
        "user_email": case.get("usuario_email") or intake.get("email") or "Sin correo",
        "user_phone": case.get("usuario_telefono") or intake.get("phone") or "Sin telefono",
        "address": case.get("usuario_direccion") or intake.get("address") or "Sin direccion registrada",
        "city": _titleish_place(case.get("usuario_ciudad") or intake.get("city")),
        "department": _titleish_place(case.get("usuario_departamento") or intake.get("department")),
    }


def _infer_health_patient_name(case: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    attachment_suggestions = _health_attachment_suggestions(case)
    direct = _clean_health_person_name(
        intake.get("represented_person_name")
        or attachment_suggestions.get("represented_person_name")
    )
    if direct:
        return direct
    uploaded_files = facts.get("uploaded_evidence_files") or []
    token_counts: dict[str, int] = {}
    ignored = {
        "registro",
        "medicamentos",
        "medicamento",
        "ayudas",
        "diagnosticas",
        "diagnosticos",
        "diagnostico",
        "historia",
        "clinica",
        "clinico",
        "orden",
        "formula",
        "respuesta",
        "eps",
        "pdf",
        "png",
        "jpg",
        "jpeg",
        "doc",
        "docx",
    }
    for file_info in uploaded_files:
        raw_name = str((file_info or {}).get("original_name") or "")
        cleaned = re.sub(r"\.[A-Za-z0-9]+$", "", raw_name)
        parts = re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{3,}", cleaned)
        for part in parts:
            lowered = part.lower()
            if lowered in ignored:
                continue
            token_counts[lowered] = token_counts.get(lowered, 0) + 1
    if not token_counts:
        return ""
    winner = max(token_counts.items(), key=lambda item: (item[1], len(item[0])))
    return _clean_health_person_name(winner[0]) if winner[1] >= 1 else ""


def _infer_health_relationship(case: dict[str, Any], patient_name: str) -> str:
    if not patient_name:
        return ""
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    explicit = str(intake.get("represented_person_relationship") or "").strip()
    if explicit:
        return explicit
    description = _normalize_writer_text(str(case.get("descripcion") or ""))
    if "mi hijo" in description or "mi hija" in description:
        return "madre y acudiente"
    acting_capacity = str(intake.get("acting_capacity") or "").strip().lower()
    special_protection = str(intake.get("special_protection") or "").strip().lower()
    if acting_capacity and acting_capacity != "nombre_propio" and special_protection == "menor de edad":
        return "acudiente"
    return ""


def _health_patient_identity_fragments(case: dict[str, Any]) -> dict[str, str]:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    attachment_context = facts.get("attachment_intelligence") or {}
    autofill = intake.get("_autofill") or {}

    typed = _health_attachment_suggestions(case)
    name = _infer_health_patient_name(case)
    age = str(
        intake.get("represented_person_age")
        or autofill.get("represented_person_age")
        or typed.get("represented_person_age")
        or ""
    ).strip()
    document_number = str(
        intake.get("represented_person_document")
        or autofill.get("represented_person_document")
        or typed.get("represented_person_document")
        or ""
    ).strip()
    birth_date = str(
        intake.get("represented_person_birth_date")
        or autofill.get("represented_person_birth_date")
        or typed.get("represented_person_birth_date")
        or ""
    ).strip()
    return {
        "name": name,
        "age": age or _infer_age_from_birth_date(birth_date),
        "document": document_number,
        "birth_date": birth_date,
    }


def _should_present_health_representation(case: dict[str, Any], patient_identity: dict[str, str]) -> bool:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    represented_person_name = str(patient_identity.get("name") or "").strip()
    represented_person_document = str(patient_identity.get("document") or "").strip()
    if not represented_person_name and not represented_person_document:
        return False
    acting_capacity = str(intake.get("acting_capacity") or "").strip().lower()
    special_protection = str(intake.get("special_protection") or "").strip().lower()
    relationship = _infer_health_relationship(case, represented_person_name)
    explicit_representation = bool(acting_capacity and acting_capacity != "nombre_propio")
    user_name = str(case.get("usuario_nombre") or intake.get("full_name") or "").strip()
    user_doc = str(case.get("usuario_documento") or intake.get("document_number") or "").strip()
    different_person = not _same_identity(user_name, represented_person_name, user_doc, represented_person_document)
    if relationship and different_person:
        return True
    if explicit_representation and different_person:
        return True
    if special_protection == "menor de edad" and different_person:
        return True
    return False


def _infer_age_from_birth_date(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    for pattern in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y"):
        try:
            born = datetime.strptime(text, pattern)
            today = datetime.now()
            years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            if years >= 0:
                return f"{years} anos"
        except ValueError:
            continue
    return ""


def _filtered_health_context_lines(case: dict[str, Any]) -> list[str]:
    raw = _dedupe_lines(_generic_facts(case))
    filtered: list[str] = []
    banned_fragments = (
        "la persona usuaria informa",
        "los hitos temporales informados",
        "las referencias temporales relevantes",
        "se identifica como entidad o destinatario involucrado",
        "frente a dicha gestion previa",
        "mi hijo",
        "mi hija",
        "correo pqrs sugerido",
        "con anterioridad, la persona usuaria presento reclamacion directa",
        "relato detallado",
        "la ia ya puede reconstruir",
        "tipo de peticion o enfoque principal",
        "tipo de peticion",
        "gestion previa resumida",
    )
    for item in raw:
        lowered = item.lower()
        if any(fragment in lowered for fragment in banned_fragments):
            continue
        stripped = lowered.strip(" .;:")
        if stripped in {"guardo silencio", "guardó silencio", "no respondieron", "no respondio", "no respondió"}:
            continue
        if lowered.startswith("hace ") and "eps" in lowered and ("medicamento" in lowered or "medicamentos" in lowered):
            continue
        filtered.append(item)
    return filtered


def _line_keywords(value: str) -> set[str]:
    stopwords = {
        "ante",
        "bajo",
        "cada",
        "como",
        "con",
        "contra",
        "cuando",
        "dicho",
        "dicha",
        "desde",
        "donde",
        "esta",
        "este",
        "esta",
        "frente",
        "hace",
        "para",
        "pero",
        "porque",
        "quien",
        "sobre",
        "sigue",
        "tiene",
        "tutela",
        "salud",
    }
    tokens = re.findall(r"[a-z0-9]{4,}", _normalize_writer_text(value))
    return {token for token in tokens if token not in stopwords}


def _is_redundant_health_line(candidate: str, existing: list[str]) -> bool:
    candidate_tokens = _line_keywords(candidate)
    if not candidate_tokens:
        return False
    for line in existing:
        line_tokens = _line_keywords(line)
        overlap = candidate_tokens & line_tokens
        if len(overlap) >= max(3, int(len(candidate_tokens) * 0.6)):
            return True
    return False


def _clean_health_raw_text(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = re.sub(r"(?i)^relato detallado:\s*", "", text).strip()
    text = re.sub(r"(?i)^correo pqrs sugerido:\s*\S+\s*", "", text).strip()
    if _normalize_writer_text(text) in {"guardo silencio", "guardó silencio", "no respondieron", "no respondio", "no respondió"}:
        return text.lower()
    return text


def _formalize_health_response(value: str) -> str:
    cleaned = _clean_health_raw_text(value)
    normalized = _normalize_writer_text(cleaned)
    if not cleaned:
        return ""
    if normalized in {"guardo silencio", "guardó silencio"}:
        return "La EPS guardo silencio y no emitio respuesta de fondo frente a la solicitud presentada."
    if normalized in {"no respondieron", "no respondio", "no respondió"}:
        return "La EPS no emitio respuesta de fondo frente a la solicitud presentada."
    return _sentence(_title_sentence(cleaned), fallback="")


def _formalize_health_urgency(case: dict[str, Any], value: str) -> str:
    cleaned = _clean_health_raw_text(value)
    if not cleaned:
        return ""
    intake = (case.get("facts") or {}).get("intake_form") or {}
    diagnosis = str(intake.get("diagnosis") or "").strip()
    treatment = _normalize_health_service_text(
        intake.get("treatment_needed") or _health_attachment_suggestions(case).get("treatment_needed") or ""
    )
    normalized = _normalize_writer_text(cleaned)
    normalized_diagnosis = _normalize_writer_text(diagnosis)
    normalized_treatment = _normalize_writer_text(treatment)
    parts: list[str] = []
    if "hace 3 meses" in normalized:
        parts.append("A la fecha de presentacion de esta accion, han transcurrido mas de tres (3) meses sin que la EPS garantice el suministro oportuno del servicio ordenado")
    elif "hace 2 meses" in normalized:
        parts.append("A la fecha de presentacion de esta accion, han transcurrido mas de dos (2) meses sin que la EPS garantice el suministro oportuno del servicio ordenado")
    if "hospital" in normalized:
        parts.append("el paciente permanece hospitalizado")
    if treatment:
        parts.append(f"sin acceso efectivo a {treatment}")
    if diagnosis:
        parts.append(f"lo que agrava el manejo clinico de {diagnosis}")
    if "falciform" in normalized_diagnosis:
        parts.append("con riesgo de crisis dolorosas, anemia persistente y complicaciones clinicas asociadas a la interrupcion del manejo hematologico")
    if "hidroxiurea" in normalized_treatment:
        parts.append("al permanecer suspendido el medicamento formulado por hematologia")
    if parts:
        return _sentence(", ".join(dict.fromkeys(parts)), fallback="")
    return _sentence(_title_sentence(cleaned), fallback="")


def _health_fact_lines(case: dict[str, Any]) -> list[str]:
    ctx = _health_context(case)
    intake = ctx["intake"]
    facts = ctx["facts"]
    attachment_suggestions = _health_attachment_suggestions(case)
    chronology_lines = _filtered_health_context_lines(case)

    acting_capacity = str(intake.get("acting_capacity") or "").strip()
    patient_identity = _health_patient_identity_fragments(case)
    represented_person_name = patient_identity["name"]
    represented_person_relationship = _infer_health_relationship(case, represented_person_name)
    represented_person_age = patient_identity["age"]
    represented_person_document = patient_identity["document"]
    represented_person_birth_date = patient_identity["birth_date"]
    target_entity = ctx["accionado"]
    diagnosis = str(intake.get("diagnosis") or attachment_suggestions.get("diagnosis") or "").strip()
    treatment_needed = _normalize_health_service_text(intake.get("treatment_needed") or attachment_suggestions.get("treatment_needed") or "")
    medical_order_date = _normalize_health_display_date(str(intake.get("medical_order_date") or attachment_suggestions.get("medical_order_date") or "").strip())
    treating_doctor_name = _clean_health_person_name(intake.get("treating_doctor_name") or intake.get("treating_physician") or attachment_suggestions.get("treating_doctor_name") or attachment_suggestions.get("treating_physician") or "")
    treating_ips_name = str(intake.get("treating_ips_name") or intake.get("ips_name") or attachment_suggestions.get("treating_ips_name") or "").strip()
    eps_request_date = _normalize_health_display_date(str(intake.get("eps_request_date") or attachment_suggestions.get("eps_request_date") or "").strip())
    eps_request_channel = str(intake.get("eps_request_channel") or "").strip()
    eps_request_reference = str(intake.get("eps_request_reference") or "").strip()
    eps_response_detail = _formalize_health_response(str(intake.get("eps_response_detail") or "").strip())
    urgency_detail = _formalize_health_urgency(case, str(intake.get("urgency_detail") or intake.get("ongoing_harm") or "").strip())
    special_protection = str(intake.get("special_protection") or "").strip()
    has_representation = _should_present_health_representation(case, patient_identity)

    lines: list[str] = []
    if represented_person_name and has_representation:
        identity_bits: list[str] = []
        if represented_person_age:
            identity_bits.append(f"de {represented_person_age}")
        if represented_person_birth_date and represented_person_birth_date != represented_person_age:
            identity_bits.append(f"nacido el {represented_person_birth_date}")
        if represented_person_document:
            identity_bits.append(f"identificado con documento No. {represented_person_document}")
        age_fragment = f", {', '.join(identity_bits)}" if identity_bits else ""
        relationship_fragment = f", en calidad de {represented_person_relationship}" if represented_person_relationship else ""
        lines.append(f"La presente accion se promueve a favor de {represented_person_name}{age_fragment}{relationship_fragment}, persona afectada por la barrera en salud aqui denunciada.")
    if medical_order_date and treatment_needed:
        doctor_fragment = f" por el medico tratante {treating_doctor_name}" if treating_doctor_name else ""
        ips_fragment = f", adscrito a {treating_ips_name}" if treating_ips_name else ""
        diagnosis_fragment = f", con ocasion del diagnostico de {diagnosis}" if diagnosis else ""
        lines.append(f"El dia {medical_order_date} fue ordenado{doctor_fragment}{ips_fragment} el servicio de salud consistente en {treatment_needed}{diagnosis_fragment}.")
    elif diagnosis or treatment_needed:
        diagnosis_fragment = f" por razon del diagnostico de {diagnosis}" if diagnosis else ""
        service_fragment = treatment_needed or "un servicio de salud requerido"
        lines.append(f"El caso gira alrededor de la necesidad de garantizar {service_fragment}{diagnosis_fragment}.")
    if eps_request_date:
        channel_fragment = f" a traves de {eps_request_channel}" if eps_request_channel else ""
        reference_fragment = f", bajo el radicado o referencia {eps_request_reference}" if eps_request_reference else ""
        lines.append(f"El dia {eps_request_date} se solicito formalmente ante {target_entity} la autorizacion o prestacion del servicio requerido{channel_fragment}{reference_fragment}.")
    if eps_response_detail:
        lines.append(f"Frente a dicha solicitud, la entidad accionada incurrio en la siguiente respuesta u omision: {_sentence(eps_response_detail)}")
    if urgency_detail:
        lines.append(f"En la actualidad persiste la siguiente afectacion o riesgo para el paciente: {_sentence(urgency_detail)}")
    if special_protection and special_protection.lower() not in {"no aplica", "ninguno"}:
        lines.append(f"La persona afectada se encuentra en condicion de especial proteccion constitucional: {special_protection}.")
    if facts.get("agent_state", {}).get("analysis", {}).get("barrier_summary"):
        for item in facts["agent_state"]["analysis"]["barrier_summary"]:
            formal_item = _formalize_health_response(str(item or "").strip())
            normalized_item = _normalize_writer_text(formal_item)
            if not formal_item:
                continue
            if normalized_item.startswith("de la narracion del caso") or "barrera administrativa atribuible a la eps" in normalized_item:
                continue
            if formal_item and not _is_redundant_health_line(formal_item, lines):
                lines.append(formal_item)

    merged = list(lines)
    for item in chronology_lines:
        if not _is_redundant_health_line(item, merged):
            merged.append(item)
    return _dedupe_lines(merged)


def _health_jurisprudence_lines(case: dict[str, Any], *, limit: int = 4) -> list[str]:
    facts = case.get("facts") or {}
    source_policy = facts.get("source_validation_policy") or {}
    precedents = [
        item
        for item in (source_policy.get("verified_sources") or [])
        if str(item.get("tipo_fuente") or "").strip() == "jurisprudencia"
    ]
    lines: list[str] = []
    for item in precedents[:limit]:
        ref = str(item.get("numero_sentencia_o_norma") or "").strip()
        corp = str(item.get("corporacion") or "").strip()
        extract = _sentence(str(item.get("extracto_relevante") or "").strip(), fallback="").strip()
        if not ref:
            continue
        if extract:
            lines.append(f"{ref} ({corp}): {extract}")
        else:
            lines.append(f"{ref} ({corp}).")
    return _dedupe_lines(lines)


def _build_financial_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}
    metadata = primary.get("metadata") or {}

    entity_name = str(intake.get("target_entity") or primary.get("name") or "Entidad financiera").strip()
    nit = str(intake.get("target_identifier") or metadata.get("nit") or "").strip()
    representative = str(intake.get("legal_representative") or metadata.get("legal_representative") or "").strip()
    target_address = str(intake.get("target_address") or metadata.get("address") or "").strip()
    pqrs_email = str(intake.get("target_pqrs_email") or primary.get("contact") or "").strip()
    notification_email = str(intake.get("target_notification_email") or "").strip()
    target_phone = str(intake.get("target_phone") or metadata.get("phone") or "").strip()
    control_entity = str(intake.get("target_superintendence") or metadata.get("superintendence") or "").strip()
    target_website = str(intake.get("target_website") or metadata.get("website") or "").strip()
    contact_parts = [item for item in [pqrs_email, notification_email] if item]
    contact = " / ".join(dict.fromkeys(contact_parts)) or target_website or "Canal oficial de atenci\u00f3n"

    user_name = _person_name(case.get("usuario_nombre"))
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin tel\u00e9fono"
    address = case.get("usuario_direccion") or "Sin direcci\u00f3n registrada"
    city = _titleish_place(case.get("usuario_ciudad"))
    department = _titleish_place(case.get("usuario_departamento"))
    formatted_header_date = (
        datetime.now()
        .strftime("%d de %B de %Y")
        .replace("January", "enero")
        .replace("February", "febrero")
        .replace("March", "marzo")
        .replace("April", "abril")
        .replace("May", "mayo")
        .replace("June", "junio")
        .replace("July", "julio")
        .replace("August", "agosto")
        .replace("September", "septiembre")
        .replace("October", "octubre")
        .replace("November", "noviembre")
        .replace("December", "diciembre")
    )

    product_type = str(intake.get("bank_product_type") or "tarjeta de cr\u00e9dito").strip()
    disputed_charge = str(intake.get("disputed_charge") or "un cobro no autorizado").strip()
    amount = str(intake.get("bank_amount_involved") or "").strip()
    parsed_amount = _parse_cop_amount(amount)
    formatted_amount = _format_cop_amount(parsed_amount) if parsed_amount is not None else amount
    refund_destination = _detect_refund_destination(intake, case)
    account_reference = _normalize_account_reference(str(intake.get("bank_account_reference") or "").strip())
    event_date = _financial_date_label(intake, facts, str(case.get("descripcion") or ""))
    prior_claim = str(intake.get("prior_claim") or "").strip().lower()
    prior_claim_date = str(intake.get("prior_claim_date") or "").strip()
    prior_claim_result = str(intake.get("prior_claim_result") or "").strip()
    chronology = _generic_facts(case)
    failures = _generic_failures(case)
    source_policy = facts.get("source_validation_policy") or {}
    source_index = _source_index_by_type(source_policy.get("verified_sources") or [])
    case_flags = _financial_case_flags(case)
    constitutional_text = _financial_constitutional_basis_text(
        [source for source in source_index["norma"] if str(source.get("numero_sentencia_o_norma") or "").startswith("Articulo")],
        has_data_issue=case_flags["has_data_issue"],
    )
    statutory_text = _financial_legal_basis_text(
        [source for source in source_index["norma"] + source_index["guia_institucional"] if not str(source.get("numero_sentencia_o_norma") or "").startswith("Articulo")],
        has_data_issue=case_flags["has_data_issue"],
        has_report_issue=case_flags["has_report_issue"],
    )
    jurisprudence_text = _financial_jurisprudence_text(source_index["jurisprudencia"])
    amount_breakdown = _financial_amount_breakdown(case, intake)
    exact_amount_known = bool(amount_breakdown["exact_known"])
    exact_total_text = str(amount_breakdown.get("exact_total_text") or "").strip()
    inferred_total_text = str(amount_breakdown.get("inferred_total_text") or "").strip()
    inferred_month_count = amount_breakdown.get("inferred_month_count")
    inferred_event_label = str(amount_breakdown.get("event_label") or event_date).strip()
    has_actual_breakdown = bool(amount_breakdown["entries"])

    chronology_lines = [
        "Soy titular del producto financiero administrado por la entidad reclamada y cuestiono formalmente los cargos descritos en este escrito.",
        f"En fecha que ubico de manera aproximada en {event_date}, advert\u00ed que el extracto de mi {product_type} registra cargos asociados a {disputed_charge}.",
        f"No otorgu\u00e9 autorizaci\u00f3n previa, expresa e informada para la inclusi\u00f3n de {disputed_charge}.",
        "La entidad no suministr\u00f3 soporte contractual, p\u00f3liza, certificado, grabaci\u00f3n, aceptaci\u00f3n digital verificable ni documento equivalente que pruebe mi consentimiento.",
        "El cobro se ha mantenido de forma sucesiva, con impacto econ\u00f3mico directo sobre mis obligaciones financieras y mi capacidad de pago.",
    ]
    if amount_breakdown["entries"]:
        chronology_lines.append(
            "De los extractos aportados se identifican, al menos, los siguientes cobros: "
            + "; ".join(f"{item['date']}: {item['amount_text']}" for item in amount_breakdown["entries"][:6])
            + "."
        )
        if exact_total_text:
            chronology_lines.append(f"Con base en esos extractos, el total actualmente consolidado asciende a {exact_total_text} COP.")
    elif formatted_amount and exact_amount_known:
        chronology_lines.append(f"El monto actualmente identificado y reportado para este cobro asciende a {formatted_amount} COP.")
        if inferred_total_text and inferred_month_count:
            chronology_lines.append(
                f"Tomando como base un cobro mensual reportado de {formatted_amount} COP desde {inferred_event_label} y hasta la fecha, "
                f"la suma acumulada reclamada asciende a {inferred_total_text} COP, correspondiente a {inferred_month_count} meses."
            )
    elif formatted_amount:
        chronology_lines.append(f"El monto actualmente identificado asciende de manera aproximada a {formatted_amount} COP, por lo que antes de escalar ante autoridades conviene consolidar el cuadro exacto de cobros con soporte en extractos.")
    else:
        chronology_lines.append("A\u00fan falta consolidar el cuadro exacto de cargos mes a mes, por lo que corresponde a la entidad certificar el valor total cobrado desde la primera facturaci\u00f3n y a la usuaria completar ese soporte con extractos si decide esperar antes de radicar.")
    if account_reference:
        chronology_lines.append(f"El producto financiero puede individualizarse como {account_reference}.")
    if prior_claim == "si" and prior_claim_date:
        chronology_lines.append(f"Antes de este escrito ya se formul\u00f3 gesti\u00f3n directa ante la entidad en fecha {prior_claim_date}.")
    if prior_claim_result:
        chronology_lines.append(f"Frente a dicha reclamaci\u00f3n previa, la respuesta o actuaci\u00f3n reportada fue la siguiente: {_sentence(prior_claim_result)}")
    elif prior_claim == "si":
        chronology_lines.append("A la fecha no existe una respuesta de fondo, completa y verificable que explique el origen del cobro o justifique su permanencia.")
    extra_chronology = [
        line
        for line in chronology
        if "persona usuaria" not in line.lower()
        and not any(token in line.lower() for token in ["cobro", "seguro", "agosto", "tarjeta", "monto", "extracto"])
    ]
    chronology_lines.extend(extra_chronology[:1])
    chronology_lines = _dedupe_lines(chronology_lines)

    failure_lines = [
        "La entidad efectu\u00f3 o mantuvo cobros sin demostrar una autorizaci\u00f3n v\u00e1lida, expresa e informada de la titular.",
        "La entidad incumpli\u00f3 su deber de informaci\u00f3n transparente, clara, verificable y suficiente sobre el producto o servicio que est\u00e1 cobrando.",
        "La entidad no acredit\u00f3 trazabilidad contractual ni soporte documental id\u00f3neo del seguro o concepto facturado.",
    ]
    if case_flags["has_report_issue"]:
        failure_lines.append("Si el cobro impact\u00f3 reportes negativos, la permanencia de esa informaci\u00f3n sin soporte suficiente compromete el habeas data financiero de la titular.")
    failure_lines.extend([line for line in failures if "persona usuaria" not in line.lower()][:1])
    failure_lines = _dedupe_lines(failure_lines)

    request_lines = [
        "CESAR de manera inmediata y definitiva el cobro no autorizado cuestionado en esta reclamaci\u00f3n.",
        (
            f"REINTEGRAR la suma exacta de {exact_total_text} COP, correspondiente a los cobros identificados en los extractos aportados, sin perjuicio de los valores adicionales que aparezcan al consolidar la totalidad del histórico."
            if exact_total_text and has_actual_breakdown
            else (
                f"REINTEGRAR la suma acumulada de {inferred_total_text} COP, calculada con base en un cobro mensual reportado de {formatted_amount} COP desde {inferred_event_label} y hasta la fecha, sin perjuicio de los ajustes que resulten del historial completo que debe certificar la entidad."
                if inferred_total_text and inferred_month_count and formatted_amount
                else "REINTEGRAR la totalidad de los valores cobrados por el concepto no autorizado desde la primera facturación identificable, con actualización e indexación a la fecha del pago."
            )
        ),
        "CERTIFICAR por escrito la eliminaci\u00f3n definitiva del cobro y entregar el historial completo de cargos, fechas, valores y referencias aplicadas.",
        "REMITIR copia \u00edntegra del soporte en el que supuestamente consta mi autorizaci\u00f3n; si dicho soporte no existe, declararlo expresamente.",
        "CORREGIR de inmediato cualquier reporte negativo derivado del cobro controvertido y remitir constancia del ajuste ante las centrales respectivas, si dicho reporte existe.",
        "INFORMAR la identidad de la aseguradora o tercero beneficiario del cobro, el n\u00famero de p\u00f3liza o producto asociado y las condiciones bajo las cuales se registr\u00f3 en el sistema de la entidad.",
    ]
    if refund_destination:
        request_lines.append(f"ABONAR la devoluci\u00f3n correspondiente en {refund_destination}, o en el canal que la entidad y la suscrita acuerden de manera verificable.")
    if not exact_amount_known:
        request_lines.append("ENTREGAR un cuadro detallado con fecha, valor y concepto de cada cobro aplicado, para definir con exactitud la suma total a devolver.")
    request_lines = _dedupe_lines(request_lines)

    response_term = (
        "De conformidad con el art\u00edculo 14 de la Ley 1755 de 2015, la presente reclamaci\u00f3n debe ser resuelta dentro de los quince (15) d\u00edas h\u00e1biles siguientes a su radicaci\u00f3n, "
        "mediante respuesta de fondo, clara, congruente y verificable."
    )
    warning_text = (
        f"En caso de silencio, respuesta evasiva o negativa infundada, la suscrita acudir\u00e1 en primer t\u00e9rmino al Defensor del Consumidor Financiero de {entity_name} y, "
        f"de persistir el incumplimiento, escalar\u00e1 la situaci\u00f3n ante {control_entity or 'la Superintendencia Financiera de Colombia'}, "
        "sin perjuicio de formular acci\u00f3n de tutela por vulneraci\u00f3n del derecho de petici\u00f3n o activar las acciones administrativas y de habeas data que correspondan."
    )
    evidence_items = _uploaded_evidence_items(case)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header_lines = [
        f"{city or 'Colombia'}, {formatted_header_date}",
        "Se\u00f1ores",
        entity_name.upper(),
    ]
    if nit:
        header_lines.append(f"NIT: {nit}")
    if representative:
        header_lines.append(f"Atenci\u00f3n: {representative}, representante legal")
    if target_address:
        header_lines.append(f"Direcci\u00f3n: {target_address}")
    header_lines.append(f"Correo: {contact}")
    if target_phone:
        header_lines.append(f"Tel\u00e9fono: {target_phone}")

    intro = (
        f"Yo, {user_name}, persona mayor de edad, titular de la c\u00e9dula de ciudadan\u00eda No. {user_doc}, con domicilio en {address}, {city}, {department}, "
        f"correo electr\u00f3nico {user_email} y tel\u00e9fono {user_phone}, actuando en calidad de titular de {product_type}, "
        f"presento la siguiente reclamaci\u00f3n formal contra {entity_name}."
    )

    return f"""{'\\n'.join(header_lines)}
Asunto: RECLAMACI\u00d3N FORMAL POR COBRO NO AUTORIZADO EN {product_type.upper()} - Art\u00edculo 23 de la Constituci\u00f3n Pol\u00edtica, Ley 1328 de 2009, Ley 1480 de 2011 y Ley 1755 de 2015

I. IDENTIFICACI\u00d3N DEL CONSUMIDOR FINANCIERO
{intro}

II. HECHOS
{_numbered_lines(chronology_lines)}

III. FUNDAMENTOS DE DERECHO
A. Fundamentos constitucionales
{constitutional_text}

B. Fundamentos legales y regulatorios
{statutory_text}

C. Jurisprudencia verificable aplicable
{jurisprudence_text}

IV. IRREGULARIDADES ATRIBUIDAS A LA ENTIDAD
{_numbered_lines(failure_lines)}

V. SOLICITUDES CONCRETAS
{_numbered_lines(request_lines)}

VI. T\u00c9RMINO LEGAL DE RESPUESTA
{response_term}

VII. ADVERTENCIA LEGAL
{warning_text}

VIII. PRUEBAS Y ANEXOS
{_numbered_lines(evidence_items)}

IX. NOTIFICACIONES
Solicito que toda respuesta, decisi\u00f3n o requerimiento relacionado con la presente reclamaci\u00f3n se remita al correo {user_email}, al tel\u00e9fono {user_phone} y, si aplica, a la direcci\u00f3n f\u00edsica {address}, {city}, {department}.

Constancia de generaci\u00f3n: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Tel\u00e9fono: {user_phone}
"""

def _build_petition_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}

    target = str(intake.get("target_entity") or primary.get("name") or _join_list(facts.get("entidades_involucradas"), fallback="Entidad destinataria")).strip()
    contact = str(primary.get("contact") or intake.get("target_pqrs_email") or intake.get("target_website") or "Canal oficial de atencion").strip()
    user_name = _person_name(case.get("usuario_nombre"))
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    address = case.get("usuario_direccion") or "Sin direccion registrada"
    city = _titleish_place(case.get("usuario_ciudad"))
    department = _titleish_place(case.get("usuario_departamento"))
    chronology = _dedupe_lines(_generic_facts(case))
    request_type = str(intake.get("request_type") or "particular").replace("_", " ").strip()
    evidence_items = _uploaded_evidence_items(case)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    header_date = (
        datetime.now()
        .strftime("%d de %B de %Y")
        .replace("January", "enero")
        .replace("February", "febrero")
        .replace("March", "marzo")
        .replace("April", "abril")
        .replace("May", "mayo")
        .replace("June", "junio")
        .replace("July", "julio")
        .replace("August", "agosto")
        .replace("September", "septiembre")
        .replace("October", "octubre")
        .replace("November", "noviembre")
        .replace("December", "diciembre")
    )

    concrete_request = str(intake.get("concrete_request") or facts.get("pretension_concreta") or "").strip()
    petition_lines: list[str] = []
    if concrete_request:
        petition_lines.append(f"RESPONDER de fondo, de manera clara, congruente y completa, la siguiente solicitud principal: {concrete_request}.")
    else:
        petition_lines.append("RESPONDER de fondo, de manera clara, congruente y completa, cada una de las solicitudes formuladas en este escrito.")
    petition_lines.append("INFORMAR por escrito las razones de hecho y de derecho que sustenten la decision adoptada frente a cada punto.")
    if contact and "canal oficial de atencion" not in contact.lower():
        petition_lines.append(f"TRAMITAR la presente peticion a traves del canal oficial identificado para la entidad destinataria: {contact}.")
    petition_lines.append(f"REMITIR la respuesta al correo {user_email} y al telefono {user_phone}, sin perjuicio de la direccion fisica informada.")
    petition_lines = _dedupe_lines(petition_lines)

    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    legal_basis_text = (
        "La presente peticion se formula en ejercicio del articulo 23 de la Constitucion Politica y de la Ley 1755 de 2015, "
        "que obligan a la entidad destinataria a emitir una respuesta de fondo, oportuna, congruente y verificable frente a los hechos y solicitudes aqui expuestos."
    )
    if verified_basis:
        legal_basis_text = f"{legal_basis_text} {verified_basis}".strip()

    facts_block = chronology or ["La persona peticionaria expone una situacion que requiere respuesta formal de la entidad destinataria."]
    intro = (
        f"Yo, {user_name}, persona mayor de edad, titular de la cedula de ciudadania No. {user_doc}, con domicilio en {address}, {city}, {department}, "
        f"correo electronico {user_email} y telefono {user_phone}, presento DERECHO DE PETICION en interes {request_type} "
        f"contra {target}, con fundamento en el articulo 23 de la Constitucion Politica y la Ley 1755 de 2015."
    )
    return f"""{city or 'Colombia'}, {header_date}
Señores
{target.upper()}
Canal oficial o sugerido: {contact}

Asunto: DERECHO DE PETICION EN INTERES {request_type.upper()}

I. IDENTIFICACION DEL PETICIONARIO
{intro}

II. HECHOS Y CONTEXTO
{_numbered_lines(facts_block)}

III. FUNDAMENTO DEL DERECHO DE PETICION
{legal_basis_text}

IV. SOLICITUDES NUMERADAS
{_numbered_lines(petition_lines)}

V. TERMINO LEGAL DE RESPUESTA
De conformidad con la Ley 1755 de 2015, la entidad destinataria debe emitir una respuesta de fondo, clara, congruente, completa y verificable dentro del termino legal aplicable al contenido de esta peticion.

VI. ANEXOS Y NOTIFICACIONES
{_numbered_lines(evidence_items)}

VII. NOTIFICACIONES
Solicito que toda respuesta, decision o requerimiento relacionado con esta peticion se remita al correo {user_email}, al telefono {user_phone} y, si aplica, a la direccion fisica {address}, {city}, {department}.

Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
"""


def _build_health_petition_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    ctx = _health_context(case)
    facts = ctx["facts"]
    intake = ctx["intake"]
    legal_analysis = ctx["legal_analysis"]
    target = ctx["accionado"]
    contact = str(ctx["primary"].get("contact") or intake.get("target_pqrs_email") or intake.get("target_website") or "Canal oficial de atencion").strip()
    chronology = _health_fact_lines(case)
    evidence_items = _uploaded_evidence_items(case)
    jurisprudence_lines = _health_jurisprudence_lines(case, limit=1)
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    diagnosis = str(intake.get("diagnosis") or "").strip()
    treatment_needed = _normalize_health_service_text(intake.get("treatment_needed") or _health_attachment_suggestions(case).get("treatment_needed") or "")
    explicit_request_lines = _split_numbered_requests(str(intake.get("numbered_requests") or "").strip())
    request_lines = explicit_request_lines or [
        f"RESPONDER de fondo, de manera clara, congruente y completa, la solicitud relacionada con {treatment_needed or 'el servicio de salud requerido'}.",
        f"AUTORIZAR o GARANTIZAR oportunamente {treatment_needed or 'el servicio de salud ordenado'}."
        if treatment_needed
        else "AUTORIZAR o GARANTIZAR oportunamente el servicio de salud requerido.",
        "INFORMAR por escrito la fecha, el canal y las condiciones en que se prestara el servicio o se resolvera la solicitud.",
        f"REMITIR la respuesta al correo {ctx['user_email']} y al telefono {ctx['user_phone']}.",
    ]
    legal_basis_text = (
        "La presente peticion se formula en ejercicio del articulo 23 de la Constitucion Politica, de la Ley 1755 de 2015 y de la Ley Estatutaria 1751 de 2015, "
        "normas que obligan a la entidad destinataria a responder de fondo y a remover barreras administrativas que impidan el acceso oportuno al servicio de salud requerido."
    )
    if diagnosis:
        legal_basis_text = f"{legal_basis_text} El caso se relaciona con el diagnostico de {diagnosis}."
    if verified_basis:
        legal_basis_text = f"{legal_basis_text} {verified_basis}".strip()
    header_date = (
        datetime.now()
        .strftime("%d de %B de %Y")
        .replace("January", "enero")
        .replace("February", "febrero")
        .replace("March", "marzo")
        .replace("April", "abril")
        .replace("May", "mayo")
        .replace("June", "junio")
        .replace("July", "julio")
        .replace("August", "agosto")
        .replace("September", "septiembre")
        .replace("October", "octubre")
        .replace("November", "noviembre")
        .replace("December", "diciembre")
    )
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    intro = (
        f"Yo, {ctx['user_name']}, persona mayor de edad, titular de la cedula de ciudadania No. {ctx['user_doc']}, con domicilio en {ctx['address']}, {ctx['city']}, {ctx['department']}, "
        f"correo electronico {ctx['user_email']} y telefono {ctx['user_phone']}, presento derecho de peticion en interes particular contra {target}."
    )
    return f"""{ctx['city'] or 'Colombia'}, {header_date}
Señores
{target.upper()}
Canal oficial identificado: {contact}

Asunto: DERECHO DE PETICION PARA GARANTIZAR SERVICIO DE SALUD

I. IDENTIFICACION DEL PETICIONARIO
{intro}

II. HECHOS Y CONTEXTO
{_numbered_lines(chronology)}

III. FUNDAMENTO DEL DERECHO DE PETICION
{legal_basis_text}

Soporte juridico complementario:
{_numbered_lines(jurisprudence_lines) if jurisprudence_lines else "1. Para esta peticion se prioriza el soporte normativo oficial suficiente y conservador."}

IV. SOLICITUDES NUMERADAS
{_numbered_lines(_dedupe_lines(request_lines))}

V. TERMINO LEGAL DE RESPUESTA
De conformidad con la Ley 1755 de 2015, la entidad destinataria debe emitir una respuesta de fondo, clara, congruente y oportuna dentro del termino legal aplicable a esta peticion.

VI. PRUEBAS Y ANEXOS
{_numbered_lines(evidence_items)}

VII. NOTIFICACIONES
Solicito que toda respuesta, decision o requerimiento relacionado con esta peticion se remita al correo {ctx['user_email']}, al telefono {ctx['user_phone']} y, si aplica, a la direccion fisica {ctx['address']}, {ctx['city']}, {ctx['department']}.

Constancia de generacion: {generated_at}

Atentamente,
{ctx['user_name']}
CC: {ctx['user_doc']}
Correo: {ctx['user_email']}
Telefono: {ctx['user_phone']}
"""


def _build_tutela_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    intake = facts.get("intake_form") or {}
    insights = facts.get("document_insights") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}

    accionado = str(intake.get("target_entity") or primary.get("name") or _join_list(facts.get("entidades_involucradas"), fallback="Entidad accionada")).strip()
    user_name = _person_name(case.get("usuario_nombre"))
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    address = case.get("usuario_direccion") or "Sin direccion registrada"
    city = _titleish_place(case.get("usuario_ciudad"))
    department = _titleish_place(case.get("usuario_departamento"))
    rights = _join_list(legal_analysis.get("derechos_vulnerados"), fallback="derechos fundamentales comprometidos")
    chronology_lines = _dedupe_lines(_generic_facts(case))
    evidence_items = _uploaded_evidence_items(case)
    procedencia = facts.get("tutela_procedencia") or {}
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    subsidiarity = _sentence(
        intake.get("tutela_other_means_detail")
        or (
            "La accion de tutela resulta necesaria por cuanto no existe otro medio judicial eficaz o, de existir, no ofrece proteccion oportuna frente al dano actual."
            if procedencia.get("subscores", {}).get("subsidiariedad") in {"alta", "media"}
            else ""
        ),
        "La accion se presenta como mecanismo de proteccion inmediata dada la insuficiencia de otros medios eficaces frente a la situacion actual.",
    )
    immediacy = _sentence(
        intake.get("tutela_immediacy_detail")
        or "La vulneracion se mantiene actual o reciente, por lo que la solicitud cumple el requisito de inmediatez.",
        "La vulneracion se mantiene actual o reciente, por lo que la solicitud cumple el requisito de inmediatez.",
    )
    no_temerity = _sentence(
        intake.get("tutela_no_temperity_detail")
        or "Bajo la gravedad del juramento manifiesto que no he presentado otra accion de tutela por los mismos hechos, derechos y pretensiones, salvo lo que se informe expresamente en este escrito.",
        "Bajo la gravedad del juramento manifiesto que no he presentado otra accion de tutela por los mismos hechos, derechos y pretensiones.",
    )
    legal_basis_text = f"{str(insights.get('legal_basis_summary') or '').strip() or 'La situacion descrita compromete derechos fundamentales y requiere proteccion judicial inmediata.'} {verified_basis}".strip()
    if str(case.get("categoria") or "").strip().lower() == "salud":
        medical_order_date = str(intake.get("medical_order_date") or "").strip()
        treating_doctor_name = str(intake.get("treating_doctor_name") or "").strip()
        treating_ips_name = str(intake.get("treating_ips_name") or intake.get("ips_name") or "").strip()
        treatment_needed = _normalize_health_service_text(intake.get("treatment_needed") or _health_attachment_suggestions(case).get("treatment_needed") or "")
        diagnosis = str(intake.get("diagnosis") or "").strip()
        eps_request_date = str(intake.get("eps_request_date") or "").strip()
        eps_request_channel = str(intake.get("eps_request_channel") or "").strip()
        eps_request_reference = str(intake.get("eps_request_reference") or "").strip()
        eps_response_detail = str(intake.get("eps_response_detail") or "").strip()
        health_lines: list[str] = []
        if medical_order_date and treatment_needed:
            doctor_fragment = f" por el medico tratante {treating_doctor_name}" if treating_doctor_name else ""
            ips_fragment = f", adscrito a {treating_ips_name}" if treating_ips_name else ""
            diagnosis_fragment = f", en razon del diagnostico de {diagnosis}" if diagnosis else ""
            health_lines.append(
                f"El dia {medical_order_date} fue ordenado{doctor_fragment}{ips_fragment} el servicio de salud consistente en {treatment_needed}{diagnosis_fragment}."
            )
        if eps_request_date:
            channel_fragment = f" a traves de {eps_request_channel}" if eps_request_channel else ""
            reference_fragment = f", bajo el radicado o referencia {eps_request_reference}" if eps_request_reference else ""
            health_lines.append(
                f"El dia {eps_request_date} se solicito formalmente ante {accionado} la autorizacion o prestacion del servicio requerido{channel_fragment}{reference_fragment}."
            )
        if eps_response_detail:
            health_lines.append(f"Frente a dicha solicitud, la EPS o entidad accionada incurrio en la siguiente respuesta u omision: {_sentence(eps_response_detail)}")
        if health_lines:
            chronology_lines = _dedupe_lines([*health_lines, *chronology_lines])
    pretensions = _generic_pretensions(case, rule["action_key"])
    tutela_requests: list[str] = []
    if pretensions:
        for line in pretensions:
            clean = _sentence(line, "").strip()
            if not clean:
                continue
            lowered = clean.lower()
            if lowered.startswith("que se "):
                clean = clean[7:].strip()
            elif lowered.startswith("que "):
                clean = clean[4:].strip()
            verb = clean.split(" ", 1)[0].upper()
            rest = clean[len(clean.split(" ", 1)[0]):].strip()
            tutela_requests.append(f"{verb} {rest}".strip())
    if not tutela_requests:
        tutela_requests = [
            "AMPARAR de manera inmediata los derechos fundamentales comprometidos en este escrito.",
            "ORDENAR a la entidad accionada la actuacion concreta necesaria para cesar la vulneracion denunciada.",
        ]
    tutela_requests = _dedupe_lines(tutela_requests)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Señor Juez Constitucional (Reparto)
{city}, {department}

Referencia: ACCION DE TUTELA PARA LA PROTECCION DE {rights.upper()}

I. COMPETENCIA Y REPARTO
Por la naturaleza de los hechos expuestos y la necesidad de proteccion inmediata de derechos fundamentales, solicito el reparto de esta accion de tutela al despacho competente.

II. IDENTIFICACION DEL ACCIONANTE Y DEL ACCIONADO
Yo, {user_name}, persona mayor de edad, titular de la cedula de ciudadania No. {user_doc}, con domicilio en {address}, {city}, {department}, correo electronico {user_email} y telefono {user_phone}, actuando en nombre propio, presento accion de tutela contra {accionado}, con fundamento en el articulo 86 de la Constitucion Politica y el Decreto 2591 de 1991.

III. HECHOS CRONOLOGICOS
{_numbered_lines(chronology_lines)}

IV. DERECHOS FUNDAMENTALES VULNERADOS
Conforme a los hechos narrados, considero comprometidos los siguientes derechos fundamentales: {rights}.

V. FUNDAMENTO JURIDICO
{legal_basis_text}

VI. PROCEDENCIA
Subsidiariedad: {subsidiarity}

Inmediatez: {immediacy}

VII. PRETENSIONES
{_numbered_lines(tutela_requests)}

VIII. PRUEBAS Y ANEXOS
{_numbered_lines(evidence_items)}

IX. JURAMENTO DE NO TEMERIDAD
{no_temerity}

X. NOTIFICACIONES
Solicito que las notificaciones del presente tramite sean remitidas al correo {user_email}, al telefono {user_phone} y, si aplica, a la direccion fisica {address}, {city}, {department}.

Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
"""


def _build_health_tutela_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    ctx = _health_context(case)
    facts = ctx["facts"]
    intake = ctx["intake"]
    attachment_suggestions = _health_attachment_suggestions(case)
    legal_analysis = ctx["legal_analysis"]
    chronology_lines = _health_fact_lines(case)
    evidence_items = _uploaded_evidence_items(case)
    jurisprudence_lines = _health_jurisprudence_lines(case, limit=2)
    rights = _join_list(
        legal_analysis.get("derechos_vulnerados"),
        fallback="los derechos fundamentales a la salud y a la vida digna",
    )
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    diagnosis = str(intake.get("diagnosis") or attachment_suggestions.get("diagnosis") or "").strip()
    treatment_needed = _normalize_health_service_text(intake.get("treatment_needed") or attachment_suggestions.get("treatment_needed") or "")
    patient_identity = _health_patient_identity_fragments(case)
    represented_person_name = patient_identity["name"]
    represented_person_relationship = _infer_health_relationship(case, represented_person_name)
    represented_person_age = patient_identity["age"]
    represented_person_document = patient_identity["document"]
    represented_person_birth_date = patient_identity["birth_date"]
    special_protection = str(intake.get("special_protection") or "").strip()
    eps_request_date = _normalize_health_display_date(str(intake.get("eps_request_date") or attachment_suggestions.get("eps_request_date") or "").strip())
    eps_request_channel = str(intake.get("eps_request_channel") or "").strip()
    eps_request_reference = str(intake.get("eps_request_reference") or "").strip()
    eps_response_detail = _formalize_health_response(str(intake.get("eps_response_detail") or "").strip())
    urgency_detail = _formalize_health_urgency(
        case,
        intake.get("urgency_detail")
        or intake.get("ongoing_harm")
        or intake.get("tutela_immediacy_detail")
        or "",
    ).strip()
    description_lower = str(case.get("descripcion") or "").lower()
    represented_fragment = ""
    has_representation = _should_present_health_representation(case, patient_identity)
    if represented_person_name and has_representation:
        identity_bits: list[str] = []
        if represented_person_age:
            identity_bits.append(f"de {represented_person_age}")
        normalized_birth_date = _normalize_health_display_date(represented_person_birth_date)
        if normalized_birth_date and normalized_birth_date != represented_person_age:
            identity_bits.append(f"nacido el {normalized_birth_date}")
        if represented_person_document:
            identity_bits.append(f"identificado con documento No. {represented_person_document}")
        elif special_protection.lower() == "menor de edad":
            identity_bits.append("identificado conforme al registro civil aportado como anexo")
        age_fragment = f", {', '.join(identity_bits)}" if identity_bits else ""
        role = "actuando en representacion"
        if represented_person_relationship:
            role = f"actuando en calidad de {represented_person_relationship}"
        elif special_protection.lower() == "menor de edad":
            role = "actuando como acudiente"
        represented_fragment = f", {role} de {represented_person_name}{age_fragment}, persona afectada por la barrera en salud descrita"
    subsidiarity_base = (
        _clean_health_raw_text(str(intake.get("tutela_other_means_detail") or "").strip())
        or (
            f"El dia {eps_request_date} se solicito ante {ctx['accionado']} la autorizacion o prestacion de {treatment_needed or 'el servicio de salud requerido'}"
            + (f" a traves de {eps_request_channel}" if eps_request_channel else "")
            + (f", bajo el radicado o referencia {eps_request_reference}" if eps_request_reference else "")
            + "."
            if eps_request_date
            else ""
        )
        or (
            f"Frente a esa gestion previa, la entidad accionada incurrio en la siguiente respuesta u omision: {_sentence(eps_response_detail)}"
            if eps_response_detail
            else ""
        )
        or "La gestion previa ante la EPS no removio la barrera actual ni garantizo el acceso oportuno al servicio ordenado."
    )
    subsidiarity = _sentence(
        f"{subsidiarity_base} Los mecanismos ordinarios ante la EPS o de reclamacion administrativa no resultan eficaces en este caso concreto, porque la proteccion requerida es inmediata y no admite una espera adicional sin agravamiento del dano.",
        "La accion de tutela resulta procedente porque la gestion previa ante la EPS no soluciono la barrera actual y la proteccion no admite mas demora.",
    )
    immediacy = _sentence(
        f"{_sentence(urgency_detail or 'La vulneracion es actual y continua, pues el servicio requerido sigue sin garantizarse y el riesgo para el paciente permanece vigente.', fallback='La vulneracion es actual y continua, pues el servicio requerido sigue sin garantizarse y el riesgo para el paciente permanece vigente.')} La accion se presenta porque la afectacion sigue vigente y requiere proteccion judicial oportuna.",
        "La vulneracion es actual y continua, pues el servicio requerido sigue sin garantizarse y el riesgo para el paciente permanece vigente.",
    )
    no_temerity = "Bajo la gravedad del juramento manifiesto que no he interpuesto otra accion de tutela por los mismos hechos, derechos y contra la misma entidad accionada, en los terminos del articulo 17 del Decreto 2591 de 1991."
    legal_basis_text = (
        "La presente accion de tutela se sustenta en el articulo 86 de la Constitucion Politica, el articulo 49 superior, la Ley Estatutaria 1751 de 2015 y el Decreto 2591 de 1991, "
        "en cuanto imponen la proteccion inmediata del derecho fundamental a la salud cuando una EPS o IPS impone barreras que impiden el acceso oportuno al servicio ordenado."
    )
    if diagnosis:
        legal_basis_text = f"{legal_basis_text} El diagnostico reportado en este caso es {diagnosis}."
    if verified_basis:
        legal_basis_text = f"{legal_basis_text} {verified_basis}".strip()
    provisional_measure = bool(
        urgency_detail
        or special_protection.lower() == "menor de edad"
        or "hospital" in description_lower
        or "hospital" in urgency_detail.lower()
    )
    tutela_requests = _dedupe_lines([
        f"AMPARAR de manera inmediata {rights}.",
        (
            f"ORDENAR como medida provisional a {ctx['accionado']} que, dentro de las cuarenta y ocho (48) horas siguientes a la notificacion de la providencia, autorice, entregue y garantice de manera efectiva {treatment_needed}."
            if provisional_measure and treatment_needed
            else ""
        ),
        (
            f"ORDENAR a {ctx['accionado']} que autorice, programe y garantice de forma efectiva {treatment_needed}."
            if treatment_needed
            else f"ORDENAR a {ctx['accionado']} que autorice, programe y garantice de forma efectiva el servicio de salud requerido."
        ),
        "GARANTIZAR el tratamiento integral, continuo y oportuno que determine el medico tratante, de conformidad con el principio de integralidad aplicable en salud.",
        "ORDENAR que la entidad accionada informe a este despacho y a la parte accionante el cumplimiento integral de lo resuelto.",
    ])
    if provisional_measure:
        tutela_requests = [
            item
            for item in tutela_requests
            if "medida provisional" not in _normalize_writer_text(item)
        ]
    if special_protection and special_protection.lower() not in {"no aplica", "ninguno"}:
        tutela_requests.append("DAR aplicacion preferente al principio de proteccion reforzada por tratarse de una persona con especial proteccion constitucional.")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""Señor Juez Constitucional (Reparto)
{ctx['city']}, {ctx['department']}

Referencia: ACCION DE TUTELA PARA LA PROTECCION DE {rights.upper()}

I. COMPETENCIA Y REPARTO
Por la naturaleza de los hechos expuestos y la necesidad de proteccion inmediata de derechos fundamentales, solicito el reparto de esta accion de tutela al despacho competente.

II. IDENTIFICACION DEL ACCIONANTE Y DEL ACCIONADO
Yo, {ctx['user_name']}, persona mayor de edad, titular de la cedula de ciudadania No. {ctx['user_doc']}, con domicilio en {ctx['address']}, {ctx['city']}, {ctx['department']}, correo electronico {ctx['user_email']} y telefono {ctx['user_phone']}{represented_fragment}, presento accion de tutela contra {ctx['accionado']}, con fundamento en el articulo 86 de la Constitucion Politica y el Decreto 2591 de 1991.

III. HECHOS CRONOLOGICOS
{_numbered_lines(chronology_lines)}

IV. DERECHOS FUNDAMENTALES VULNERADOS
Conforme a los hechos narrados, considero comprometidos los siguientes derechos fundamentales: {rights}.

V. FUNDAMENTO JURIDICO
{legal_basis_text}

Jurisprudencia verificable aplicable:
{_numbered_lines(jurisprudence_lines) if jurisprudence_lines else "1. Para este caso se prioriza fundamento normativo oficial suficiente."}

VI. PROCEDENCIA
Subsidiariedad: {subsidiarity}

Inmediatez: {immediacy}

VII. SOLICITUD DE MEDIDA PROVISIONAL
{("Con fundamento en el articulo 7 del Decreto 2591 de 1991, solicito que se adopte medida provisional inmediata para evitar la prolongacion del dano actual mientras se decide de fondo la presente accion, en especial mediante la entrega, autorizacion o prestacion urgente del servicio de salud requerido." if provisional_measure else "No se formula medida provisional independiente, sin perjuicio de que el despacho adopte las ordenes urgentes que estime necesarias para evitar la prolongacion del dano actual.")}

VIII. PRETENSIONES
{_numbered_lines(tutela_requests)}

IX. PRUEBAS Y ANEXOS
{_numbered_lines(evidence_items)}

X. JURAMENTO DE NO TEMERIDAD
{no_temerity}

XI. NOTIFICACIONES
Solicito que las notificaciones del presente tramite sean remitidas al correo {ctx['user_email']}, al telefono {ctx['user_phone']} y, si aplica, a la direccion fisica {ctx['address']}, {ctx['city']}, {ctx['department']}.

Constancia de generacion: {generated_at}

Atentamente,
{ctx['user_name']}
CC: {ctx['user_doc']}
Correo: {ctx['user_email']}
Telefono: {ctx['user_phone']}
"""


def _build_health_impugnacion_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    ctx = _health_context(case)
    intake = ctx["intake"]
    facts = ctx["facts"]
    legal_analysis = ctx["legal_analysis"]
    chronology_lines = _health_fact_lines(case)
    ruling_date = _normalize_health_display_date(str(intake.get("tutela_ruling_date") or "").strip()) or "fecha que debe precisarse con la notificacion del fallo"
    court_name = str(intake.get("tutela_court_name") or "").strip() or "el despacho judicial que decidio la primera instancia"
    ruling_result = str(intake.get("tutela_decision_result") or "").strip() or "decision desfavorable a la parte accionante"
    appeal_reason = str(intake.get("tutela_appeal_reason") or "").strip() or "El fallo no valoro integralmente la urgencia del caso ni la barrera actual de la EPS."
    treatment_needed = _normalize_health_service_text(intake.get("treatment_needed") or _health_attachment_suggestions(case).get("treatment_needed") or "") or "el servicio de salud requerido"
    diagnosis = str(intake.get("diagnosis") or "").strip()
    urgency_detail = _formalize_health_urgency(
        case,
        intake.get("urgency_detail") or intake.get("ongoing_harm") or "",
    ).strip()
    jurisprudence_lines = _health_jurisprudence_lines(case, limit=2)
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""Señor Juez Constitucional de Segunda Instancia
{ctx['city']}, {ctx['department']}

Referencia: IMPUGNACION DE TUTELA EN SALUD

I. IDENTIFICACION DEL FALLO IMPUGNADO
Por medio del presente escrito impugno el fallo de tutela proferido por {court_name} y notificado el {ruling_date}, relacionado con el expediente de salud promovido contra {ctx['accionado']}. La decision controvertida correspondio a: {ruling_result}.

II. PARTES
Accionante: {ctx['user_name']}, CC {ctx['user_doc']}
Accionada: {ctx['accionado']}

III. HECHOS RELEVANTES DEL TRAMITE
{_numbered_lines(chronology_lines)}

IV. RAZONES DE IMPUGNACION
1. El fallo impugnado no valoro de manera suficiente la afectacion actual del paciente ni la necesidad de proteccion inmediata frente a {treatment_needed}.
2. Motivo principal de desacuerdo: {_sentence(appeal_reason)}
3. La decision cuestionada no aprecio integralmente los soportes medicos ni la barrera administrativa atribuida a la entidad accionada.
4. {f"El caso involucra el diagnostico de {diagnosis}, circunstancia que exigia un examen reforzado de continuidad, oportunidad y riesgo actual." if diagnosis else "El expediente exigia un examen reforzado de continuidad, oportunidad y riesgo actual en salud."}
5. {(
    f"La afectacion actual persiste porque {str(_sentence(urgency_detail, fallback='')).strip().rstrip('.').lower()}."
    if urgency_detail
    else "La afectacion actual persiste, por lo que la proteccion judicial sigue siendo necesaria y oportuna."
)}

V. FUNDAMENTO JURIDICO
La impugnacion se presenta al amparo del articulo 86 de la Constitucion Politica y del Decreto 2591 de 1991, en procura de una segunda revision judicial integral del caso. {verified_basis}

Soporte juridico complementario:
{_numbered_lines(jurisprudence_lines) if jurisprudence_lines else "1. Para esta impugnacion se prioriza soporte normativo y jurisprudencial conservador."}

VI. SOLICITUDES A LA SEGUNDA INSTANCIA
1. REVOCAR o MODIFICAR el fallo impugnado en lo desfavorable a la parte accionante.
2. CONCEDER la proteccion integral de los derechos fundamentales comprometidos.
3. ORDENAR a {ctx['accionado']} el cumplimiento efectivo de la prestacion en salud requerida, en especial {treatment_needed}.
4. VALORAR integralmente la historia clinica, la orden medica y el riesgo actual que permanece vigente.

VII. PRUEBAS Y ANEXOS
{_numbered_lines(_uploaded_evidence_items(case))}

VIII. NOTIFICACIONES
Solicito que las notificaciones se remitan al correo {ctx['user_email']}, al telefono {ctx['user_phone']} y, si aplica, a la direccion fisica {ctx['address']}, {ctx['city']}, {ctx['department']}.

Constancia de generacion: {generated_at}

Atentamente,
{ctx['user_name']}
CC: {ctx['user_doc']}
"""


def _build_health_desacato_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    ctx = _health_context(case)
    intake = ctx["intake"]
    facts = ctx["facts"]
    legal_analysis = ctx["legal_analysis"]
    chronology_lines = _health_fact_lines(case)
    ruling_date = _normalize_health_display_date(str(intake.get("tutela_ruling_date") or "").strip()) or "fecha que debe precisarse con el fallo"
    court_name = str(intake.get("tutela_court_name") or "").strip() or "el juzgado de primera instancia"
    order_summary = str(intake.get("tutela_order_summary") or "").strip() or "garantizar el servicio de salud requerido"
    noncompliance = _sentence(str(intake.get("tutela_noncompliance_detail") or "").strip(), fallback="La entidad accionada no ha cumplido integralmente la orden judicial de salud y la barrera persiste.")
    treatment_needed = _normalize_health_service_text(intake.get("treatment_needed") or _health_attachment_suggestions(case).get("treatment_needed") or "") or "el servicio de salud requerido"
    jurisprudence_lines = _health_jurisprudence_lines(case, limit=2)
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return f"""Señor Juez Constitucional de Primera Instancia
{ctx['city']}, {ctx['department']}

Referencia: INCIDENTE DE DESACATO EN SALUD

I. IDENTIFICACION DEL FALLO Y DE LA ORDEN INCUMPLIDA
Promuevo incidente de desacato respecto del fallo de tutela proferido por {court_name} y notificado el {ruling_date}, dentro del tramite adelantado contra {ctx['accionado']}, por cuanto la orden judicial consistente en {order_summary} no ha sido cumplida.

II. HECHOS POSTERIORES AL FALLO
{_numbered_lines(chronology_lines)}

III. INCUMPLIMIENTO ACTUAL
{noncompliance}

IV. ORDEN JUDICIAL DESATENDIDA
La orden cuyo cumplimiento se solicita de manera inmediata consistio en {order_summary}, relacionada con {treatment_needed}. Pese a la notificacion del fallo, la barrera en salud persiste y la afectacion del paciente continua.

V. FUNDAMENTO JURIDICO
El presente incidente se formula con fundamento en el articulo 86 de la Constitucion Politica y en el regimen del Decreto 2591 de 1991 aplicable al desacato por incumplimiento de fallos de tutela. {verified_basis}

Soporte juridico complementario:
{_numbered_lines(jurisprudence_lines) if jurisprudence_lines else "1. Para este incidente se prioriza soporte normativo verificable sobre cumplimiento del fallo."}

VI. SOLICITUDES
1. DECLARAR que existe incumplimiento del fallo de tutela referido.
2. ORDENAR el cumplimiento inmediato e integral de la decision judicial.
3. REQUERIR a la entidad y al funcionario responsable para que acrediten cumplimiento efectivo, inmediato y verificable.
4. ADOPTAR las medidas de apremio o sancion que resulten procedentes frente al responsable del incumplimiento.

VII. PRUEBAS Y ANEXOS
{_numbered_lines(_uploaded_evidence_items(case))}

VIII. NOTIFICACIONES
Solicito que las notificaciones se remitan al correo {ctx['user_email']}, al telefono {ctx['user_phone']} y, si aplica, a la direccion fisica {ctx['address']}, {ctx['city']}, {ctx['department']}.

Constancia de generacion: {generated_at}

Atentamente,
{ctx['user_name']}
CC: {ctx['user_doc']}
"""


def _build_generic_document(case: dict[str, Any], rule: dict[str, Any]) -> str:
    facts = case.get("facts") or {}
    insights = facts.get("document_insights") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    primary = routing.get("primary_target") or {}
    user_name = _person_name(case.get("usuario_nombre"))
    user_doc = case.get("usuario_documento") or "Sin documento registrado"
    user_email = case.get("usuario_email") or "Sin correo"
    user_phone = case.get("usuario_telefono") or "Sin telefono"
    address = case.get("usuario_direccion") or "Sin direccion registrada"
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    target = str(primary.get("name") or _join_list(facts.get("entidades_involucradas"), fallback="la autoridad o entidad competente")).strip()
    contact = str(primary.get("contact") or "Canal por definir").strip()
    chronology_text = _paragraph_lines(_generic_facts(case))
    failures_text = _paragraph_lines(_generic_failures(case))
    pretensions = _generic_pretensions(case, rule["action_key"])
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    legal_basis = str(insights.get("legal_basis_summary") or "").strip() or (
        f"El caso se sustenta en los siguientes derechos o intereses comprometidos: {_join_list(legal_analysis.get('derechos_vulnerados'))}."
    )
    if verified_basis:
        legal_basis = f"{legal_basis} {verified_basis}".strip()
    evidence_text = _join_list(_uploaded_evidence_items(case), fallback="Copia del documento de identidad de la persona usuaria.")
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Senores
{target}
Canal sugerido: {contact}

Referencia: {rule['document_title']}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con correo {user_email}, telefono {user_phone} y residencia en {address}, {city}, {department}, presento el siguiente escrito formal.

{_section("DESTINATARIO", f"El presente documento se dirige a {target}, como autoridad o entidad llamada a responder por los hechos aqui descritos.")}
{_section("HECHOS Y CRONOLOGIA", chronology_text)}
{_section("FALLAS O VULNERACIONES ATRIBUIDAS", failures_text)}
{_section("FUNDAMENTO JURIDICO", legal_basis)}
{_section("PRETENSIONES O SOLICITUDES CONCRETAS", _numbered_lines(pretensions))}
{_section("PRUEBAS Y ANEXOS", f"Como soportes del presente escrito se anuncian o aportan los siguientes elementos: {evidence_text}.")}
{_section("NOTIFICACIONES", f"Solicito que toda respuesta o decision relacionada con este asunto sea comunicada al correo {user_email} y al telefono {user_phone}.")}
Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
"""


def build_document(case: dict[str, Any]) -> str:
    rule = get_document_rule(case.get("recommended_action"), case.get("workflow_type"))
    is_health_block = str(case.get("categoria") or case.get("category") or "").strip().lower() == "salud"
    if is_health_block:
        if rule["action_key"] == "accion de tutela":
            return _build_health_tutela_document(case, rule)
        if rule["action_key"] == "impugnacion de tutela":
            return _build_health_impugnacion_document(case, rule)
        if rule["action_key"] == "incidente de desacato":
            return _build_health_desacato_document(case, rule)
        if "derecho de peticion" in rule["action_key"]:
            return _build_health_petition_document(case, rule)
    if rule["action_key"] == "accion de tutela":
        return _build_tutela_document(case, rule)
    if rule["action_key"] in {"reclamacion financiera", "derecho de peticion financiero"}:
        return _build_financial_document(case, rule)
    if "derecho de peticion" in rule["action_key"]:
        return _build_petition_document(case, rule)
    return _build_generic_document(case, rule)
