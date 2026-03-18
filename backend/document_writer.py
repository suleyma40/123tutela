from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

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


def _titleish_place(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text == text.lower():
        return " ".join(part.capitalize() for part in text.split())
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
    exact_known = bool(entries) or (bool(raw_amount) and not _amount_looks_approximate(raw_amount) and parsed_raw is not None)
    return {
        "entries": entries,
        "total": total,
        "raw_amount": raw_amount,
        "parsed_raw": parsed_raw,
        "exact_total_text": _format_cop_amount(total if total is not None else parsed_raw),
        "exact_known": exact_known,
    }


def _uploaded_evidence_items(case: dict[str, Any]) -> list[str]:
    facts = case.get("facts") or {}
    uploaded_files = facts.get("uploaded_evidence_files") or []
    items = ["Copia del documento de identidad de la reclamante."]
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
        "Sentencia C-909 de 2012": "La Corte admitió límites intensos frente a estipulaciones o prácticas abusivas en relaciones de consumo y financieras.",
        "Sentencia T-517 de 2006": "La actividad aseguradora y financiera, por su interés público, no puede amparar abusos informativos ni afectaciones desproporcionadas al usuario.",
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
            f"REINTEGRAR la suma exacta de {exact_total_text} COP, correspondiente a los cobros identificados en los extractos aportados, sin perjuicio de los valores adicionales que aparezcan al consolidar la totalidad del hist\u00f3rico."
            if exact_total_text
            else "REINTEGRAR la totalidad de los valores cobrados por el concepto no autorizado desde la primera facturaci\u00f3n identificable, con actualizaci\u00f3n e indexaci\u00f3n a la fecha del pago."
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
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    chronology_text = _paragraph_lines(_generic_facts(case))
    pretensions = _generic_pretensions(case, rule["action_key"])
    evidence_text = _join_list(_uploaded_evidence_items(case), fallback="Copia del documento de identidad del peticionario.")
    request_type = str(intake.get("request_type") or "interes particular").replace("_", " ").strip()
    verified_basis = str(
        legal_analysis.get("legal_basis_verified_summary")
        or ((facts.get("source_validation_policy") or {}).get("legal_basis_verified_summary") or "")
    ).strip()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Senores
{target}
Canal sugerido: {contact}

Asunto: Derecho de peticion de {request_type}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con domicilio en {address}, {city}, {department}, correo electronico {user_email} y telefono {user_phone}, en ejercicio del derecho fundamental de peticion consagrado en el articulo 23 de la Constitucion Politica y desarrollado por la Ley 1755 de 2015, presento la siguiente solicitud.

{_section("IDENTIFICACION DEL PETICIONARIO", f"Nombre: {user_name}\nCedula: {user_doc}\nCorreo: {user_email}\nTelefono: {user_phone}\nDireccion: {address}, {city}, {department}")}
{_section("HECHOS Y CONTEXTO", chronology_text)}
{_section("FUNDAMENTO DEL DERECHO DE PETICION", f"La presente peticion se formula para obtener una respuesta de fondo, clara, congruente y completa sobre los hechos y solicitudes aqui expuestos. {verified_basis}".strip())}
{_section("SOLICITUDES NUMERADAS", _numbered_lines(pretensions))}
{_section("TERMINO DE RESPUESTA", "Solicito respuesta de fondo dentro de los terminos legales aplicables conforme a la Ley 1755 de 2015.")}
{_section("ANEXOS Y NOTIFICACIONES", f"Como soporte de esta peticion se anuncian o se aportan los siguientes elementos: {evidence_text}.")}
{_section("NOTIFICACIONES", f"Solicito que la respuesta sea enviada al correo {user_email} y al telefono {user_phone}.")}
Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
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
    city = case.get("usuario_ciudad") or ""
    department = case.get("usuario_departamento") or ""
    rights = _join_list(legal_analysis.get("derechos_vulnerados"), fallback="derechos fundamentales comprometidos")
    chronology_text = _paragraph_lines(_generic_facts(case))
    pretensions = _generic_pretensions(case, rule["action_key"])
    evidence_text = _join_list(_uploaded_evidence_items(case), fallback="Copia del documento de identidad del accionante.")
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
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return f"""Senor Juez Constitucional (Reparto)
{city}, {department}

Referencia: Accion de tutela para la proteccion de {rights}

Yo, {user_name}, identificado(a) con cedula {user_doc}, con domicilio en {address}, {city}, {department}, correo electronico {user_email} y telefono {user_phone}, actuando en nombre propio, presento accion de tutela contra {accionado}, con fundamento en el articulo 86 de la Constitucion Politica y el Decreto 2591 de 1991.

{_section("COMPETENCIA Y REPARTO", "Por la naturaleza de los hechos y la necesidad de proteccion inmediata de derechos fundamentales, solicito el reparto de esta accion de tutela al despacho competente.")}
{_section("ACCIONADO", f"La presente solicitud se dirige contra {accionado}, por los hechos y omisiones que se exponen a continuacion.")}
{_section("HECHOS CRONOLOGICOS", chronology_text)}
{_section("DERECHOS FUNDAMENTALES VULNERADOS", f"Conforme a los hechos narrados, considero comprometidos los siguientes derechos fundamentales: {rights}.")}
{_section("FUNDAMENTO JURIDICO", legal_basis_text)}
{_section("PROCEDENCIA", f"Subsidiariedad: {subsidiarity}\n\nInmediatez: {immediacy}")}
{_section("PRETENSIONES", _numbered_lines(pretensions))}
{_section("PRUEBAS Y ANEXOS", f"Como soporte de la presente accion se anuncian o se aportan los siguientes elementos: {evidence_text}.")}
{_section("JURAMENTO DE NO TEMERIDAD", no_temerity)}
{_section("NOTIFICACIONES", f"Solicito que las notificaciones del presente tramite sean remitidas al correo {user_email} y al telefono {user_phone}.")}
Constancia de generacion: {generated_at}

Atentamente,
{user_name}
CC: {user_doc}
Correo: {user_email}
Telefono: {user_phone}
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
    if rule["action_key"] == "accion de tutela":
        return _build_tutela_document(case, rule)
    if rule["action_key"] in {"reclamacion financiera", "derecho de peticion financiero"}:
        return _build_financial_document(case, rule)
    if "derecho de peticion" in rule["action_key"]:
        return _build_petition_document(case, rule)
    return _build_generic_document(case, rule)
