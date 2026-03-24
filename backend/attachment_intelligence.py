from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any
from urllib import error, request

from backend.config import settings
from backend.storage import absolute_path

try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None

try:
    from docx import Document  # type: ignore
except Exception:  # pragma: no cover
    Document = None


def _read_pdf(path: Path) -> str:
    if PdfReader is None:
        return ""
    try:
        reader = PdfReader(str(path))
        chunks: list[str] = []
        total_chars = 0
        for page in reader.pages[:24]:
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append(text)
                total_chars += len(text)
            if total_chars >= 80000:
                break
        return "\n".join(chunks)
    except Exception:
        return ""


def _read_pdf_with_claude(path: Path, *, file_name: str, typed_suggestions: dict[str, Any]) -> dict[str, Any] | None:
    if not settings.anthropic_api_key:
        return None
    try:
        pdf_bytes = path.read_bytes()
    except Exception:
        return None
    if not pdf_bytes:
        return None

    prompt = {
        "task": (
            "Lee este PDF medico colombiano, aunque sea escaneado o tenga OCR deficiente, "
            "y produce una sintesis juridico-clinica util para tutela o derecho de peticion en salud."
        ),
        "instructions": [
            "Prioriza identidad del paciente, fechas, medicos, IPS/EPS, diagnosticos, barreras y riesgo actual.",
            "Si detectas historia clinica, reconstruye una cronologia probatoria breve con fechas exactas si aparecen.",
            "Si una parte del PDF es ruido u OCR deficiente, ignorala.",
            "No inventes hechos ni nombres.",
            "Responde solo JSON valido.",
            (
                "Devuelve exactamente estas llaves: summary, chronology, dates_detected, focus, "
                "medication_order_confirmed, barrier_summary, risk_summary, patient_name, patient_document, "
                "requested_service, entities_detected, treating_doctor_name, treating_ips_name, key_excerpts."
            ),
        ],
        "evidence_name": file_name,
        "typed_suggestions": typed_suggestions,
    }
    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 2200,
        "temperature": 0,
        "system": (
            "Eres un analista clinico-juridico colombiano. Lees PDFs medicos y produces una sintesis "
            "estructurada y util para litigio en salud."
        ),
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "base64",
                            "media_type": "application/pdf",
                            "data": base64.b64encode(pdf_bytes).decode("ascii"),
                        },
                    },
                    {
                        "type": "text",
                        "text": json.dumps(prompt, ensure_ascii=False),
                    },
                ],
            }
        ],
    }
    raw_request = request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(raw_request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    content = body.get("content") or []
    text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
    if not text_parts:
        return None
    try:
        parsed = json.loads("".join(text_parts))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    chronology = [str(item).strip() for item in (parsed.get("chronology") or []) if str(item).strip()]
    excerpts = [str(item).strip() for item in (parsed.get("key_excerpts") or []) if str(item).strip()]
    reconstructed_text = " ".join(
        [
            "Historia clinica analizada por Claude.",
            str(parsed.get("summary") or "").strip(),
            str(parsed.get("barrier_summary") or "").strip(),
            str(parsed.get("risk_summary") or "").strip(),
            " ".join(chronology[:10]),
            " ".join(excerpts[:8]),
        ]
    ).strip()
    parsed["source"] = "anthropic_pdf"
    parsed["attachment_based"] = True
    parsed["reconstructed_text"] = re.sub(r"\s+", " ", reconstructed_text).strip()
    return parsed


def _infer_name_from_filename(file_name: str) -> str:
    stem = Path(str(file_name or "")).stem
    cleaned = re.sub(r"[_\-]+", " ", stem)
    cleaned = re.sub(r"\(\d+\)", " ", cleaned)
    cleaned = re.sub(r"(?i)\b(registro|civil|tarjeta|identidad|documento|pdf|scan|escaneado|anexo)\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    parts = [part for part in cleaned.split(" ") if len(part) > 1]
    if not parts:
        return ""
    candidate = " ".join(parts[:4]).strip()
    return candidate.title() if len(candidate) >= 3 else ""


def _clean_person_candidate(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;")
    if not text:
        return ""
    lowered = text.lower()
    banned_fragments = (
        "atencion",
        "atención",
        "plan",
        "historia clinica",
        "historia clínica",
        "medicamento",
        "formula",
        "fórmula",
        "ips",
        "eps",
        "aneurisma",
        "consulta",
        "servicio",
    )
    if any(fragment in lowered for fragment in banned_fragments):
        return ""
    if len(re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ]{2,}", text)) < 2:
        return ""
    return " ".join(part.capitalize() for part in text.split())


def _normalize_health_service_candidate(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;")
    if not text:
        return ""
    corrections = {
        "moujarou": "Mounjaro",
        "moujaro": "Mounjaro",
        "mounjaro": "Mounjaro",
        "emdicamento": "medicamento",
    }
    lowered = text.lower()
    for wrong, right in corrections.items():
        lowered = lowered.replace(wrong, right.lower())
    text = re.sub(r"(?i)^el\\s+", "", lowered).strip()
    words = text.split()
    if len(words) <= 3 and all(word.replace("-", "").isalpha() for word in words):
        return " ".join(word.capitalize() for word in words)
    return text[:1].upper() + text[1:]


def _clean_health_entity_candidate(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;")
    if not text:
        return ""
    text = re.sub(r"(?i)^(ips|eps|clinica|hospital|centro medico)\s+", "", text).strip()
    if len(text) < 3:
        return ""
    return " ".join(part.capitalize() for part in text.split())


def _normalize_ascii_text(value: Any) -> str:
    text = str(value or "")
    return text.encode("ascii", "ignore").decode("ascii")


def _dedupe_lines(items: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for item in items:
        clean = re.sub(r"\s+", " ", str(item or "")).strip(" .,:;")
        if not clean:
            continue
        key = clean.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(clean)
    return ordered


def _health_lines_from_text(text: str) -> list[str]:
    chunks = re.split(r"[\r\n]+", str(text or ""))
    lines: list[str] = []
    for chunk in chunks:
        normalized = re.sub(r"\s+", " ", chunk).strip(" .,:;")
        if len(normalized) < 12:
            continue
        lines.append(normalized)
    return lines


def _extract_health_dates(text: str) -> list[str]:
    matches = re.findall(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text)
    long_matches = re.findall(r"\b\d{1,2}\s+de\s+[A-Za-z ]+\s+de\s+\d{4}\b", text, flags=re.IGNORECASE)
    dates = matches + long_matches
    ordered: list[str] = []
    seen: set[str] = set()
    for item in dates:
        clean = re.sub(r"\s+", " ", item).strip()
        lowered = clean.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        ordered.append(clean)
    return ordered


def _extract_doctor_name_from_line(line: str) -> str:
    candidate = _pick_first(
        [
            r"\b(?:dr\.|dra\.|doctor|doctora|medico tratante|m[eé]dico tratante)[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{5,80})",
            r"\b(?:atendido por|valorado por|evaluado por)[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{5,80})",
        ],
        line,
    )
    return _clean_person_candidate(candidate)


def _extract_medical_registration_from_line(line: str) -> str:
    candidate = _pick_first(
        [
            r"\b(?:rm|reg(?:istro)?\s*(?:medico|m[eé]dico|profesional)|tarjeta\s+profesional)\s*[:#]?\s*([A-Za-z0-9\-]{4,30})",
            r"\b(?:registro|matricula)\s*(?:medica|m[eé]dica|profesional)?\s*[:#]?\s*([A-Za-z0-9\-]{4,30})",
        ],
        line,
    )
    return re.sub(r"\s+", " ", str(candidate or "")).strip(" .,:;#")


def _extract_order_from_line(line: str) -> str:
    candidate = _pick_first(
        [
            r"\b(?:conducta|plan|se formula|se prescribe|se ordena|ordena|prescribe|recomienda|recomendacion|recomendación)[:\s]+([^\.]{12,180})",
            r"\b(?:medicamento|tratamiento|manejo)\s+([A-Za-zÁÉÍÓÚáéíóúÑñ0-9 \-]{6,120})",
        ],
        line,
    )
    cleaned = re.sub(r"\s+", " ", str(candidate or "")).strip(" .,:;")
    return cleaned


def _extract_specialty_from_line(line: str) -> str:
    candidate = _pick_first(
        [
            r"\bconsulta(?: externa)? de\s+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{4,60})",
            r"\bvaloracion(?: por)?\s+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{4,60})",
            r"\b(?:endocrinologia|endocrinología|medicina interna|neurocirugia|neurocirugía|cirugia vascular|cirugía vascular|neurologia|neurología|programa de obesidad)\b",
        ],
        line,
    )
    cleaned = re.sub(r"\s+", " ", str(candidate or "")).strip(" .,:;")
    return cleaned[:1].upper() + cleaned[1:] if cleaned else ""


def _extract_health_consultation_events(lines: list[str], *, patient_name: str = "") -> list[str]:
    events: list[str] = []
    seen: set[str] = set()
    for line in lines:
        normalized = re.sub(r"\s+", " ", str(line or "")).strip(" .,:;")
        lowered = _normalize_ascii_text(normalized).lower()
        if not _is_viable_health_chronology_line(normalized):
            continue
        if not _extract_health_dates(normalized):
            continue
        if not any(
            token in lowered
            for token in (
                "consulta",
                "valoracion",
                "valoración",
                "teleconcepto",
                "evolucion",
                "evolución",
                "endocrino",
                "medicina interna",
                "programa de obesidad",
                "neuro",
                "cirugia",
                "cirugía",
            )
        ):
            continue
        date = _extract_health_dates(normalized)[0]
        doctor_name = _extract_doctor_name_from_line(normalized)
        medical_registration = _extract_medical_registration_from_line(normalized)
        specialty = _extract_specialty_from_line(normalized)
        order_excerpt = _extract_order_from_line(normalized)
        patient_fragment = f"{patient_name} " if patient_name else "la paciente "
        doctor_fragment = ""
        if doctor_name:
            doctor_fragment = f" por {doctor_name}"
            if medical_registration:
                doctor_fragment += f" (registro {medical_registration})"
        order_fragment = f" En esa atencion se indico {order_excerpt}." if order_excerpt and len(order_excerpt) >= 12 else ""
        if "teleconcepto" in lowered:
            event = f"El {date}, {patient_fragment}fue valorada mediante teleconcepto{f' de {specialty}' if specialty else ''}{doctor_fragment}.{order_fragment}"
        elif specialty:
            event = f"El {date}, {patient_fragment}asistio a consulta de {specialty}{doctor_fragment}."
            event = f"{event}{order_fragment}"
        elif doctor_name:
            event = f"El {date}, {patient_fragment}fue valorada{doctor_fragment}.{order_fragment}"
        else:
            event = f"El {date} se registro una atencion clinica relevante en la historia medica.{order_fragment}"
        event = re.sub(r"\s+", " ", event).strip()
        event = event.replace("..", ".")
        key = _normalize_ascii_text(event).lower()
        if key in seen:
            continue
        seen.add(key)
        events.append(event)
    return events[:12]


def _extract_health_identity(text: str, typed_suggestions: dict[str, Any]) -> dict[str, str]:
    patient_name = _clean_person_candidate(
        str(
            typed_suggestions.get("represented_person_name")
            or typed_suggestions.get("patient_name")
            or ""
        )
    )
    if not patient_name:
        patient_name = _clean_person_candidate(
            _pick_first(
                [
                    r"informaci[oó]n b[aá]sica del paciente(?: y la atenci[oó]n)?\s+plan[:\s]+\w+\s+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{8,80})\s+identificaci[oó]n",
                    r"plan[:\s]+\w+\s+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{8,80})\s+identificaci[oó]n",
                    r"\b(?:paciente|nombre del paciente|nombre|usuario|accionante)[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{8,120})",
                    r"\b([A-Z][A-Z ]{10,120})\b",
                ],
                text,
            )
        )

    patient_document = str(
        typed_suggestions.get("represented_person_document")
        or typed_suggestions.get("patient_document")
        or ""
    ).strip()
    if not patient_document:
        patient_document = _pick_first(
            [
                r"sexo\s+(?:cc|ti|ce|nuip)\s*([0-9.\-]{6,20})\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
                r"identificaci[oó]n\s+fecha de nacimiento\s+edad(?: en la atenci[oó]n)?\s+sexo\s+(?:cc|ti|ce|nuip)\s*([0-9.\-]{6,20})",
                r"\b(?:cc|cedula|cédula|documento|identificacion|identificación|ti|nuip)[:\s#-]*([0-9.\-]{6,20})",
            ],
            text,
        )

    return {
        "patient_name": patient_name,
        "patient_document": patient_document,
    }


def _extract_health_entities(text: str) -> list[str]:
    candidates = re.findall(
        r"\b(?:eps|ips|clinica|clínica|hospital|comfama|sura|san vicente|pablo tobon|modofisio)\s*[A-Za-z&.\- ]{0,60}",
        text,
        flags=re.IGNORECASE,
    )
    cleaned: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        item = re.sub(r"\s+", " ", raw).strip(" .,:;")
        if len(item) < 4:
            continue
        key = _normalize_ascii_text(item).lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)
    return cleaned[:6]


def _extract_health_barrier_summary(text: str) -> str:
    lowered = _normalize_ascii_text(text).lower()
    if all(term in lowered for term in ("endocrino", "medicina interna")) and any(
        term in lowered for term in ("programa de obesidad", "no pertinencia", "proxima cita", "6 meses", "remision")
    ):
        return (
            "Los soportes muestran un circulo burocratico entre endocrinologia, medicina interna y programa de obesidad, "
            "sin decision terapeutica definitiva y con nueva cita diferida por varios meses."
        )
    if any(term in lowered for term in ("no pertinencia", "teleconcepto")):
        return "Los soportes muestran devoluciones o respuestas de no pertinencia que impiden una solucion clinica oportuna."
    if any(term in lowered for term in ("negado", "no autorizado", "sin autorizacion")):
        return "Los soportes muestran una negativa o falta de autorizacion frente al servicio de salud requerido."
    if any(term in lowered for term in ("sin cita", "demora", "agenda", "sin agenda")):
        return "Los soportes muestran una demora relevante en la valoracion o programacion del servicio requerido."
    return ""


def _extract_health_risk_summary(text: str) -> str:
    lowered = _normalize_ascii_text(text).lower()
    if "aneurisma" in lowered and any(term in lowered for term in ("ruptura", "riesgo vital", "fatal", "cirugia", "abdominal")):
        return "La historia clinica describe un riesgo vital actual asociado a aneurisma cerebral y a la imposibilidad de corregirlo oportunamente."
    if any(term in lowered for term in ("oncologia", "quimioterapia", "cancer")):
        return "La historia clinica muestra riesgo grave por interrupcion de tratamiento oncologico."
    if any(term in lowered for term in ("hospitalizado", "uci", "urgencias")):
        return "La historia clinica muestra una afectacion actual severa con necesidad de atencion prioritaria."
    return ""


def _extract_health_service_need(text: str, typed_suggestions: dict[str, Any]) -> str:
    explicit = _normalize_health_service_candidate(str(typed_suggestions.get("treatment_needed") or "").strip())
    if explicit:
        return explicit
    lowered = _normalize_ascii_text(text).lower()
    if "aneurisma" in lowered and any(term in lowered for term in ("programa de obesidad", "medicina interna", "no pertinencia", "6 meses", "endocrino")):
        return "valoracion prioritaria y definicion del manejo integral para la reduccion de peso requerida para la correccion del aneurisma cerebral"
    candidate = _pick_first(
        [
            r"\b(?:medicamento|tratamiento|procedimiento|cirugia|cirugía|valoracion|valoración|consulta)\s+([A-Za-z0-9ÁÉÍÓÚáéíóúÑñ \-]{3,120})",
            r"\b(mounjaro|tirzepatida|semaglutida|hidroxiurea)\b",
        ],
        text,
    )
    return _normalize_health_service_candidate(candidate)


def _is_viable_health_chronology_line(line: str) -> bool:
    normalized = re.sub(r"\s+", " ", str(line or "")).strip(" .,:;")
    if len(normalized) < 20 or len(normalized) > 260:
        return False
    lowered = _normalize_ascii_text(normalized).lower()
    banned_fragments = (
        "informacion basica del paciente",
        "informacion confidencial",
        "fecha de impresion",
        "antecedentes generales",
        "grupo poblacional",
        "telefono responsable",
        "estado civil",
        "patologia presenta observacion",
        "nacidos vivos",
        "embarazo",
        "ecografia",
        "feto",
        "placenta",
        "cordon 3 vasos",
        "historia clinica",
    )
    if any(fragment in lowered for fragment in banned_fragments):
        return False
    if normalized.count(":") >= 4 or normalized.count(",") >= 10:
        return False
    digit_chars = sum(1 for char in normalized if char.isdigit())
    if digit_chars and digit_chars / max(len(normalized), 1) > 0.28:
        return False
    return True


def _extract_health_chronology(lines: list[str]) -> list[str]:
    chronology: list[str] = []
    seen: set[str] = set()
    trigger_words = (
        "consulta",
        "valoracion",
        "valoración",
        "remite",
        "remision",
        "remisión",
        "teleconcepto",
        "no pertinencia",
        "programa de obesidad",
        "endocrino",
        "endocrinologia",
        "endocrinología",
        "medicina interna",
        "aneurisma",
        "mounjaro",
        "tirzepat",
        "cirugia",
        "cirugía",
    )
    for line in lines:
        lowered = _normalize_ascii_text(line).lower()
        if not _is_viable_health_chronology_line(line):
            continue
        if not any(word in lowered for word in trigger_words):
            continue
        if not _extract_health_dates(line) and not any(term in lowered for term in ("hace 6 meses", "6 meses", "proxima cita", "próxima cita")):
            continue
        normalized = re.sub(r"\s+", " ", line).strip()
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        chronology.append(normalized)
    return chronology[:10]


def _detect_health_case_focus(text: str) -> str:
    lowered = _normalize_ascii_text(text).lower()
    if all(term in lowered for term in ("endocrino", "medicina interna")) and any(
        term in lowered
        for term in ("no pertinencia", "programa de obesidad", "remite", "remision", "6 meses", "proxima cita")
    ):
        return "circulo_burocratico"
    if any(term in lowered for term in ("desacato", "incumplimiento fallo", "incumplio orden")):
        return "desacato"
    if any(term in lowered for term in ("niega", "negado", "no autorizado", "sin autorizacion")):
        return "negacion_directa"
    if any(term in lowered for term in ("sin cita", "valoracion", "valoración", "no pertinencia")):
        return "barrera_de_acceso"
    return "salud_general"


def _deterministic_health_case_synthesis(*, combined_text: str, evidence_names: list[str], typed_suggestions: dict[str, Any]) -> dict[str, Any]:
    lines = _health_lines_from_text(combined_text)
    identity = _extract_health_identity(combined_text, typed_suggestions)
    chronology = _extract_health_chronology(lines)
    consultation_events = _extract_health_consultation_events(lines, patient_name=identity.get("patient_name") or "")
    dates = _extract_health_dates(combined_text)
    diagnosis = str(typed_suggestions.get("diagnosis") or "").strip()
    treatment = _extract_health_service_need(combined_text, typed_suggestions)
    doctor = str(typed_suggestions.get("treating_doctor_name") or typed_suggestions.get("treating_physician") or "").strip()
    ips_name = str(typed_suggestions.get("treating_ips_name") or "").strip()
    focus = _detect_health_case_focus(combined_text)
    barrier_summary = _extract_health_barrier_summary(combined_text)
    risk_summary = _extract_health_risk_summary(combined_text)
    entities = _extract_health_entities(combined_text)
    lowered = _normalize_ascii_text(combined_text).lower()
    if focus == "circulo_burocratico":
        synthesized_chronology: list[str] = []
        if "aneurisma" in lowered:
            synthesized_chronology.append("La historia clinica registra aneurisma cerebral y la necesidad de una ruta clinica prioritaria para permitir la correccion quirurgica.")
        if "programa de obesidad" in lowered:
            synthesized_chronology.append("Endocrinologia o las atenciones relacionadas remitieron al programa de obesidad para definir el manejo de reduccion de peso.")
        if "no pertinencia" in lowered or "teleconcepto" in lowered:
            synthesized_chronology.append("Medicina interna devolvio el caso con respuesta de no pertinencia, sin definir una conducta terapeutica de fondo.")
        if "6 meses" in lowered or "proxima cita" in lowered:
            synthesized_chronology.append("La nueva cita con endocrinologia fue diferida por varios meses, manteniendo la barrera actual sin solucion clinica oportuna.")
        chronology = _dedupe_lines(consultation_events + synthesized_chronology + chronology)[:10]
    else:
        chronology = _dedupe_lines(consultation_events + chronology)[:10]
    medication_order_confirmed = bool(
        typed_suggestions.get("medical_order_date")
        or re.search(r"\b(?:se formula|se prescribe)\b", combined_text, flags=re.IGNORECASE)
        or re.search(r"\b(?:orden medica|formula medica|prescribi[oó]|orden[oó])\b", combined_text, flags=re.IGNORECASE)
    )
    summary_parts: list[str] = []
    if identity["patient_name"]:
        summary_parts.append(f"Paciente detectado en soportes: {identity['patient_name']}.")
    if identity["patient_document"]:
        summary_parts.append(f"Documento detectado en soportes: {identity['patient_document']}.")
    if diagnosis:
        summary_parts.append(f"Diagnostico principal detectado: {diagnosis}.")
    if treatment:
        summary_parts.append(f"Servicio o manejo mencionado en los soportes: {treatment}.")
    if doctor:
        summary_parts.append(f"Profesional identificado en soportes: {doctor}.")
    if ips_name:
        summary_parts.append(f"IPS o institucion referida en soportes: {ips_name}.")
    if focus == "circulo_burocratico":
        summary_parts.append("Los anexos muestran un circulo burocratico entre especialidades o remisiones internas sin solucion clinica definitiva.")
    elif focus == "negacion_directa":
        summary_parts.append("Los anexos sugieren una negativa o falta de autorizacion frente al servicio reclamado.")
    elif focus == "barrera_de_acceso":
        summary_parts.append("Los anexos muestran barreras de acceso, demora o falta de valoracion oportuna.")
    if barrier_summary:
        summary_parts.append(barrier_summary)
    if risk_summary:
        summary_parts.append(risk_summary)
    if dates:
        summary_parts.append("Fechas detectadas en soportes: " + ", ".join(dates[:6]) + ".")
    return {
        "source": "deterministic",
        "focus": focus,
        "chronology": chronology,
        "dates_detected": dates,
        "summary": " ".join(summary_parts).strip(),
        "evidence_names": evidence_names[:6],
        "patient_name": identity["patient_name"],
        "patient_document": identity["patient_document"],
        "entities_detected": entities,
        "requested_service": treatment,
        "barrier_summary": barrier_summary,
        "risk_summary": risk_summary,
        "medication_order_confirmed": medication_order_confirmed,
        "attachment_based": True,
    }


def _llm_health_case_synthesis(*, combined_text: str, evidence_names: list[str], typed_suggestions: dict[str, Any]) -> dict[str, Any] | None:
    if not settings.anthropic_api_key or not combined_text.strip():
        return None
    prompt = {
        "task": "Leer historia clinica y soportes de un caso de salud en Colombia y producir una sintesis cronologica util para tutela o derecho de peticion.",
        "instructions": [
            "Prioriza los anexos sobre el relato del usuario.",
            "No inventes hechos ni nombres.",
            "Si no hay orden formal del medicamento o procedimiento, dilo claramente.",
            "Detecta si el patron principal es negacion directa, circulo burocratico, falta de valoracion, demora o continuidad de tratamiento.",
            "Responde solo JSON con: summary, chronology, dates_detected, focus, medication_order_confirmed, barrier_summary, risk_summary, patient_name, patient_document, requested_service, entities_detected.",
        ],
        "evidence_names": evidence_names[:8],
        "typed_suggestions": typed_suggestions,
        "combined_text": combined_text[:60000],
    }
    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 1200,
        "temperature": 0,
        "system": "Eres un analista clinico-juridico estricto. Sintetiza historias clinicas colombianas para documentos de salud sin inventar datos.",
        "messages": [{"role": "user", "content": json.dumps(prompt, ensure_ascii=False)}],
    }
    raw_request = request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(raw_request, timeout=25) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    content = body.get("content") or []
    text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
    if not text_parts:
        return None
    try:
        parsed = json.loads("".join(text_parts))
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    parsed["source"] = "anthropic"
    parsed["attachment_based"] = True
    return parsed


def _read_docx(path: Path) -> str:
    if Document is None:
        return ""
    try:
        document = Document(str(path))
        parts = [(paragraph.text or "").strip() for paragraph in document.paragraphs[:240]]
        return "\n".join([item for item in parts if item])
    except Exception:
        return ""


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def extract_file_text(file_record: dict[str, Any]) -> str:
    relative_path = str(file_record.get("relative_path") or "").strip()
    if not relative_path:
        return ""
    path = absolute_path(relative_path)
    if not path.exists():
        return ""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".docx":
        return _read_docx(path)
    if suffix in {".txt", ".md", ".csv"}:
        return _read_text(path)
    return ""


def _merge_health_synthesis_into_suggestions(
    suggestions: dict[str, Any],
    synthesis: dict[str, Any] | None,
) -> dict[str, Any]:
    merged = dict(suggestions or {})
    if not synthesis:
        return merged
    mapping = {
        "patient_name": "represented_person_name",
        "patient_document": "represented_person_document",
        "requested_service": "treatment_needed",
        "treating_doctor_name": "treating_doctor_name",
        "treating_ips_name": "treating_ips_name",
        "risk_summary": "urgency_detail",
        "barrier_summary": "eps_response_detail",
    }
    for source_key, target_key in mapping.items():
        value = str(synthesis.get(source_key) or "").strip()
        if value and not merged.get(target_key):
            merged[target_key] = value
    return merged


def _normalize_health_match_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _normalize_ascii_text(value).lower()).strip()


def _pick_preferred_health_entity(
    typed_suggestions: dict[str, Any],
    entities_detected: list[str],
) -> str:
    explicit = str(typed_suggestions.get("target_entity") or typed_suggestions.get("eps_name") or "").strip()
    if explicit:
        return explicit
    if not entities_detected:
        return ""
    ranked = sorted(
        entities_detected,
        key=lambda item: (
            "eps" not in _normalize_health_match_key(item),
            "ips" in _normalize_health_match_key(item),
            len(item),
        ),
    )
    return str(ranked[0]).strip()


def _build_health_evidence_record(
    *,
    typed_suggestions: dict[str, Any],
    health_case_synthesis: dict[str, Any],
    attachment_profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    def _plausible_patient_name(value: str) -> str:
        cleaned = _clean_person_candidate(value)
        lowered = _normalize_health_match_key(cleaned)
        banned = ("diagnostico", "principal", "atencion", "consulta", "orden medica", "historia clinica")
        return "" if any(token in lowered for token in banned) else cleaned

    def _plausible_entity(value: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;")
        lowered = _normalize_health_match_key(cleaned)
        if not cleaned:
            return ""
        if not any(token in lowered for token in ("eps", "ips", "clinica", "hospital", "comfama", "sura", "sanitas", "famisanar", "compensar", "nueva eps")):
            return ""
        if any(token in lowered for token in ("demora", "autorizacion", "solucion", "consulta del", "paciente con", "mantiene")):
            return ""
        return cleaned

    def _plausible_service(value: str) -> str:
        cleaned = _normalize_health_service_candidate(str(value or "").strip())
        lowered = _normalize_health_match_key(cleaned)
        if not cleaned:
            return ""
        if len(lowered) < 8:
            return ""
        if any(token in lowered for token in ("orden medica del", "consulta del", "historia clinica", "diagnostico principal", "del 16", "del 10")):
            return ""
        return cleaned

    def _plausible_diagnosis(value: str) -> str:
        cleaned = re.sub(r"\s+", " ", str(value or "")).strip(" .,:;")
        lowered = _normalize_health_match_key(cleaned)
        if not cleaned:
            return ""
        if any(token in lowered for token in ("diagnostico principal", "barrera de acceso", "necesidad de atencion", "medicina interna")):
            return ""
        return cleaned

    synthesis = health_case_synthesis or {}
    chronology = [str(item).strip() for item in (synthesis.get("chronology") or []) if str(item).strip()]
    dates_detected = [str(item).strip() for item in (synthesis.get("dates_detected") or []) if str(item).strip()]
    entities_detected = [str(item).strip() for item in (synthesis.get("entities_detected") or []) if str(item).strip()]
    support_types = [
        str((profile or {}).get("type") or "").strip()
        for profile in (attachment_profiles or [])
        if str((profile or {}).get("type") or "").strip()
    ]
    patient_name = _plausible_patient_name(
        str(
            typed_suggestions.get("represented_person_name")
            or synthesis.get("patient_name")
            or ""
        )
    )
    patient_document = str(
        typed_suggestions.get("represented_person_document")
        or synthesis.get("patient_document")
        or ""
    ).strip()
    requested_service = _plausible_service(
        str(
            typed_suggestions.get("treatment_needed")
            or synthesis.get("requested_service")
            or ""
        ).strip()
    )
    diagnosis = _plausible_diagnosis(str(typed_suggestions.get("diagnosis") or "").strip())
    barrier_summary = str(
        typed_suggestions.get("eps_response_detail")
        or synthesis.get("barrier_summary")
        or ""
    ).strip()
    risk_summary = str(
        typed_suggestions.get("urgency_detail")
        or typed_suggestions.get("ongoing_harm")
        or synthesis.get("risk_summary")
        or ""
    ).strip()
    target_entity = _plausible_entity(_pick_preferred_health_entity(typed_suggestions, entities_detected))
    medical_order_date = str(typed_suggestions.get("medical_order_date") or "").strip()
    treating_doctor_name = str(
        typed_suggestions.get("treating_doctor_name")
        or typed_suggestions.get("treating_physician")
        or synthesis.get("treating_doctor_name")
        or ""
    ).strip()
    treating_ips_name = str(
        typed_suggestions.get("treating_ips_name")
        or synthesis.get("treating_ips_name")
        or ""
    ).strip()
    support_strength = "strong" if any(item in {"historia_clinica", "formula"} for item in support_types) else "medium" if support_types else "weak"
    return {
        "patient_name": patient_name,
        "patient_document": patient_document,
        "target_entity": target_entity,
        "entities_detected": entities_detected[:6],
        "diagnosis": diagnosis,
        "requested_service": requested_service,
        "medical_order_date": medical_order_date,
        "treating_doctor_name": treating_doctor_name,
        "treating_ips_name": treating_ips_name,
        "barrier_summary": barrier_summary,
        "risk_summary": risk_summary,
        "chronology": chronology[:10],
        "dates_detected": dates_detected[:10],
        "support_types": support_types[:6],
        "support_strength": support_strength,
        "attachment_based": bool(patient_name or requested_service or chronology or entities_detected),
    }


def _classify_attachment_type(file_name: str, compact_text: str) -> str:
    lowered = f"{file_name} {compact_text}".lower()
    if any(term in lowered for term in ["radicado", "pqrs", "derecho de peticion", "derecho de petición", "reclamo"]):
        return "radicado"
    if any(term in lowered for term in ["extracto", "estado de cuenta", "movimiento", "tarjeta terminada", "cuenta terminada"]):
        return "extracto"
    if any(term in lowered for term in ["formula medica", "formula médica", "orden medica", "orden médica", "receta"]):
        return "formula"
    if any(term in lowered for term in ["historia clinica", "historia clínica", "epicrisis", "evolucion", "evolución"]):
        return "historia_clinica"
    if any(term in lowered for term in ["datacredito", "data credito", "cifin", "central de riesgo", "reporte negativo"]):
        return "reporte_riesgo"
    return "general"


def _extract_attachment_suggestions(file_name: str, compact_text: str) -> dict[str, Any]:
    attachment_type = _classify_attachment_type(file_name, compact_text)
    suggestions: dict[str, Any] = {"attachment_type": attachment_type}
    lowered_name = str(file_name or "").lower()

    represented_person_name = _pick_first(
        [
            r"\b(?:nombre del paciente|paciente|nombre|nombres y apellidos)[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{5,80})",
        ],
        compact_text,
    )
    if not represented_person_name and any(term in lowered_name for term in ["registro", "jeronimo", "tarjeta", "identidad"]):
        represented_person_name = _infer_name_from_filename(file_name)
    represented_person_name = _clean_person_candidate(represented_person_name)
    if represented_person_name:
        suggestions["represented_person_name"] = represented_person_name
    if not suggestions.get("represented_person_name"):
        info_block_name = _clean_person_candidate(
            _pick_first(
                [
                    r"informaci[oó]n b[aá]sica del paciente(?: y la atenci[oó]n)?\s+plan[:\s]+\w+\s+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{8,80})\s+identificaci[oó]n",
                    r"plan[:\s]+\w+\s+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{8,80})\s+identificaci[oó]n",
                ],
                compact_text,
            )
        )
        if info_block_name:
            suggestions["represented_person_name"] = info_block_name

    represented_person_document = _pick_first(
        [
            r"sexo\s+(?:cc|ti|ce|nuip)\s*([0-9.\-]{6,20})\s+\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            r"\b(?:tarjeta de identidad|ti|registro civil|nuip|identificacion|identificación)[:\s#-]*([0-9.\-]{6,20})",
        ],
        compact_text,
    )
    if represented_person_document:
        suggestions["represented_person_document"] = represented_person_document
    represented_person_email = _pick_first(
        [r"correo electr[oó]nico\s+([A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,})"],
        compact_text,
    )
    if represented_person_email:
        suggestions["represented_person_email"] = represented_person_email
    represented_person_address = _pick_first(
        [r"direcci[oó]n\s+([A-Za-z0-9 #\-.,]{8,120})\s+correo electr[oó]nico"],
        compact_text,
    )
    if represented_person_address:
        suggestions["represented_person_address"] = re.sub(r"\s+", " ", represented_person_address).strip()
    phone_matches = re.findall(r"\b3\d{9}\b|\b\d{7}\b", compact_text)
    if phone_matches:
        suggestions["represented_person_phone"] = " / ".join(phone_matches[:3])

    birth_date = _pick_first(
        [
            r"\b(?:fecha de nacimiento|nacio el|nacimiento)[:\s]+([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
            r"\b(?:fecha de nacimiento|nacio el|nacimiento)[:\s]+([0-9]{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóúñÑ]+\s+de\s+[0-9]{4})",
        ],
        compact_text,
    )
    if birth_date:
        suggestions["represented_person_birth_date"] = birth_date
        suggestions.setdefault("represented_person_age", birth_date)

    age = _pick_first(
        [
            r"\bedad[:\s]+([0-9]{1,2}\s*(?:años|anos))\b",
            r"\b([0-9]{1,2}\s*(?:años|anos))\b",
        ],
        compact_text,
    )
    if age and not suggestions.get("represented_person_age"):
        suggestions["represented_person_age"] = age
    if not compact_text and any(term in lowered_name for term in ["registro", "tarjeta", "identidad", "nuip"]):
        suggestions["identity_support_unreadable"] = "si"

    physician = _pick_first(
        [
            r"\b(?:medico tratante|médico tratante|hematologo|hematólogo|doctor|doctora|dr\.|dra\.)[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{5,80})",
        ],
        compact_text,
    )
    physician = _clean_person_candidate(physician)
    if physician:
        suggestions["treating_physician"] = physician

    lowered_compact = compact_text.lower()
    if any(term in lowered_compact for term in ["hospitalizado", "hospitalizacion", "hospitalización", "urgencias", "uci", "internado"]):
        suggestions.setdefault(
            "ongoing_harm",
            "El paciente se encuentra hospitalizado o ha requerido atencion hospitalaria reciente, lo que evidencia un riesgo actual y la necesidad de proteccion inmediata.",
        )

    if attachment_type == "radicado":
        suggestions["prior_claim"] = "si"
        radicado_date = _pick_first(
            [
                r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
                r"\b(\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+\s+de\s+\d{4})\b",
            ],
            compact_text,
        )
        if radicado_date:
            suggestions["prior_claim_date"] = radicado_date
        radicado_ref = _pick_first(
            [
                r"\bradicado[:\s#-]*([A-Z0-9\-]{5,40})\b",
                r"\bpqrs[:\s#-]*([A-Z0-9\-]{5,40})\b",
            ],
            compact_text,
        )
        if radicado_ref:
            suggestions["case_reference"] = radicado_ref
        claim_result = _pick_first(
            [
                r"\b(no\s+(?:ha\s+)?respondid[oa][^\.]{0,120})",
                r"\b(negad[oa][^\.]{0,120})",
                r"\b(respuesta[^\.]{0,120})",
            ],
            compact_text,
        )
        if claim_result:
            suggestions["prior_claim_result"] = claim_result

    if attachment_type == "extracto":
        amount = _pick_first([r"(\$\s?\d[\d\.\,]{2,})", r"(\d[\d\.\,]{3,}\s?(?:pesos|cop))"], compact_text)
        if amount:
            suggestions["bank_amount_involved"] = amount
        event_date = _pick_first(
            [
                r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
                r"\b(\d{1,2}\s+de\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+\s+de\s+\d{4})\b",
            ],
            compact_text,
        )
        if event_date:
            suggestions["bank_event_date"] = event_date
        account_reference = _pick_first(
            [
                r"\b(?:terminada|terminado)\s+en\s+(\d{4})\b",
                r"\b(?:cuenta|tarjeta)[^\d]{0,12}(\d{4})\b",
            ],
            compact_text,
        )
        if account_reference:
            suggestions["bank_account_reference"] = f"Terminada en {account_reference}"
        disputed_charge = _pick_first(
            [
                r"\b(seguro de [A-Za-zÁÉÍÓÚáéíóúÑñ ]{3,40}|cuota de manejo|interes de mora|cargo no reconocido|cobro no autorizado)\b",
            ],
            compact_text,
        )
        if disputed_charge:
            suggestions["disputed_charge"] = disputed_charge

    if attachment_type in {"formula", "historia_clinica"}:
        diagnosis = _pick_first(
            [
                r"\bdiagnostico[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ,.\-]{5,100})",
                r"\bimpresion diagnostica[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ0-9 ,.\-]{5,100})",
            ],
            compact_text,
        )
        if diagnosis:
            diagnosis = re.split(r"\.\s+(?:medicamento|formula|orden|tratamiento)\b", diagnosis, maxsplit=1, flags=re.IGNORECASE)[0].strip(" .,:;")
            suggestions["diagnosis"] = diagnosis
        treatment_needed = _pick_first(
            [
                r"\b(medicamento [A-Za-zÁÉÍÓÚáéíóúÑñ0-9 \-]{3,80})\b",
                r"\b(procedimiento [A-Za-zÁÉÍÓÚáéíóúÑñ0-9 \-]{3,80})\b",
                r"\b(cita con [A-Za-zÁÉÍÓÚáéíóúÑñ0-9 \-]{3,80})\b",
                r"\b(orden medica [A-Za-zÁÉÍÓÚáéíóúÑñ0-9 \-]{3,80})\b",
            ],
            compact_text,
        )
        if treatment_needed:
            normalized_treatment = _normalize_health_service_candidate(treatment_needed)
            if normalized_treatment:
                suggestions["treatment_needed"] = normalized_treatment
        if not suggestions.get("treatment_needed"):
            direct_medication = _pick_first(
                [
                    r"\b(mounjaro|moujaro|moujarou|hidroxiurea|semaglutida|tirzepatida)\b",
                    r"\b(?:prescribieron|prescribio|formularon|formulo|ordenaron|ordeno)\s+(?:el\s+)?(?:medicamento\s+)?([A-Za-z0-9 \-]{3,80})\b",
                ],
                compact_text,
            )
            normalized_direct_medication = _normalize_health_service_candidate(direct_medication)
            if normalized_direct_medication:
                suggestions["treatment_needed"] = normalized_direct_medication
        medical_order_date = _pick_first(
            [
                r"\b(?:fecha de orden|fecha de formula|fecha de formulacion|emitida el|prescrito el|ordenado el)[:\s]*([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
                r"\b(?:fecha de orden|fecha de formula|fecha de formulacion|emitida el|prescrito el|ordenado el)[:\s]*([0-9]{1,2}\s+de\s+[A-Za-z0-9 ]+\s+de\s+[0-9]{4})",
            ],
            compact_text,
        )
        if medical_order_date:
            suggestions["medical_order_date"] = medical_order_date
        doctor_name = _clean_person_candidate(
            _pick_first(
                [
                    r"\b(?:internista|endocrinologo|endocrinologa|neurocirujano|cirujano vascular|medico tratante|medico|doctor|doctora)[:\s]+([A-Za-z ]{5,80})",
                    r"\bdr\.?\s+([A-Za-z ]{5,80})",
                    r"\bdra\.?\s+([A-Za-z ]{5,80})",
                ],
                compact_text,
            )
        )
        if doctor_name:
            suggestions["treating_doctor_name"] = doctor_name
        ips_name = _clean_health_entity_candidate(
            _pick_first(
                [
                    r"\b(?:ips|clinica|hospital|centro medico)\s+([A-Za-z&.\- ]{3,60})",
                    r"\b(comfama|sura|san vicente|pablo tobon|modofisio)\b",
                ],
                compact_text,
            )
        )
        if ips_name:
            suggestions["treating_ips_name"] = ips_name
        if any(term in lowered_compact for term in ["hospitalizado", "hospitalizacion", "hospitalización", "crisis vasooclusiva", "riesgo vital", "sin suspender"]):
            suggestions.setdefault(
                "urgency_detail",
                "La historia clinica y los soportes medicos muestran un riesgo actual para la salud del paciente, con necesidad de continuidad inmediata del tratamiento ordenado por el medico tratante.",
            )

    if attachment_type == "reporte_riesgo":
        disputed_data = _pick_first(
            [
                r"\b(reporte negativo[^\.]{0,120})",
                r"\b(obligacion[^\.]{0,120}mora[^\.]{0,120})",
            ],
            compact_text,
        )
        if disputed_data:
            suggestions["disputed_data"] = disputed_data
        suggestions["requested_data_action"] = "corregir o eliminar el reporte"

    return suggestions


def build_attachment_context(file_records: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_names = [str(item.get("original_name") or "").strip() for item in file_records if item.get("original_name")]
    extracted_chunks: list[str] = []
    combined_text_parts: list[str] = []
    attachment_profiles: list[dict[str, Any]] = []
    typed_suggestions: dict[str, Any] = {}
    pdf_health_syntheses: list[dict[str, Any]] = []

    for item in file_records:
        text = extract_file_text(item)
        compact = re.sub(r"\s+", " ", text).strip() if text else ""
        file_name = str(item.get("original_name") or "").strip()
        profile = _extract_attachment_suggestions(file_name, compact)
        profile_type = str((profile or {}).get("attachment_type") or "general")
        if not compact and profile_type in {"historia_clinica", "formula"}:
            relative_path = str(item.get("relative_path") or "").strip()
            path = absolute_path(relative_path) if relative_path else None
            if path and path.exists() and path.suffix.lower() == ".pdf":
                pdf_health_synthesis = _read_pdf_with_claude(
                    path,
                    file_name=file_name,
                    typed_suggestions=typed_suggestions,
                )
                if pdf_health_synthesis:
                    pdf_health_syntheses.append(pdf_health_synthesis)
                    compact = re.sub(r"\s+", " ", str(pdf_health_synthesis.get("reconstructed_text") or "")).strip()
                    profile = _merge_health_synthesis_into_suggestions(profile, pdf_health_synthesis)
        if profile:
            attachment_profiles.append(
                {
                    "name": file_name,
                    "type": profile.pop("attachment_type", "general"),
                    "suggestions": profile,
                }
            )
            for key, value in profile.items():
                if value and not typed_suggestions.get(key):
                    typed_suggestions[key] = value
        if compact:
            combined_text_parts.append(compact[:18000])
            extracted_chunks.append(f"Archivo {item.get('original_name')}: {compact[:900]}")

    combined_text = " ".join(combined_text_parts)
    lowered = combined_text.lower()
    clues: list[str] = []

    if any(term in lowered for term in ["registro civil", "tarjeta de identidad", "menor de edad", "acudiente", "madre del menor", "padre del menor"]):
        clues.append("Los anexos sugieren que el caso involucra a un menor de edad o persona representada.")
    if any(term in lowered for term in ["formula medica", "orden medica", "historia clinica", "diagnostico", "medicamento", "dosis"]):
        clues.append("Los anexos contienen informacion medica relevante sobre diagnostico, formula o tratamiento.")
    if any(term in lowered for term in ["eps", "autorizacion", "negado", "pendiente", "medicamentos"]):
        clues.append("Los anexos parecen mostrar relacion con EPS, autorizaciones o negacion de servicios de salud.")

    health_case_synthesis: dict[str, Any] = pdf_health_syntheses[0] if pdf_health_syntheses else {}
    health_signal_present = any(
        term in lowered
        for term in [
            "historia clinica",
            "historia clínica",
            "formula medica",
            "formula médica",
            "diagnostico",
            "diagnóstico",
            "eps",
            "ips",
            "cirugia",
            "cirugía",
            "aneurisma",
            "medicina interna",
            "endocrino",
        ]
    ) or any(str((profile or {}).get("type") or "").strip() in {"historia_clinica", "formula"} for profile in attachment_profiles)
    if health_signal_present:
        synthesized = _llm_health_case_synthesis(
            combined_text=combined_text,
            evidence_names=evidence_names,
            typed_suggestions=typed_suggestions,
        ) or _deterministic_health_case_synthesis(
            combined_text=combined_text,
            evidence_names=evidence_names,
            typed_suggestions=typed_suggestions,
        )
        if synthesized:
            if health_case_synthesis:
                merged = dict(health_case_synthesis)
                for key, value in synthesized.items():
                    if value and not merged.get(key):
                        merged[key] = value
                health_case_synthesis = merged
            else:
                health_case_synthesis = synthesized

    health_evidence_record = _build_health_evidence_record(
        typed_suggestions=typed_suggestions,
        health_case_synthesis=health_case_synthesis,
        attachment_profiles=attachment_profiles,
    ) if health_case_synthesis or typed_suggestions else {}

    return {
        "evidence_names": evidence_names,
        "extracted_text_available": bool(combined_text_parts),
        "combined_text": combined_text[:60000],
        "summary_lines": extracted_chunks[:4],
        "clues": clues,
        "attachment_profiles": attachment_profiles[:6],
        "typed_suggestions": typed_suggestions,
        "health_case_synthesis": health_case_synthesis,
        "health_evidence_record": health_evidence_record,
    }


def enrich_description_with_attachment_context(description: str, context: dict[str, Any] | None) -> str:
    if not context:
        return description

    parts = [description.strip()]
    evidence_names = context.get("evidence_names") or []
    summary_lines = context.get("summary_lines") or []
    clues = context.get("clues") or []

    if evidence_names:
        parts.append("Anexos cargados: " + ", ".join(evidence_names) + ".")
    if clues:
        parts.append("Hallazgos preliminares de anexos: " + " ".join(clues))
    if summary_lines:
        parts.append("Extractos utiles de anexos:\n" + "\n".join(summary_lines))

    return "\n\n".join([item for item in parts if item])


def _pick_first(patterns: list[str], text: str) -> str:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            value = next((group for group in match.groups() if group), "")
            if value:
                return re.sub(r"\s+", " ", value).strip(" .,:;")
    return ""


def suggest_fields_from_context(
    *,
    category: str | None,
    description: str,
    form_data: dict[str, Any] | None,
    attachment_context: dict[str, Any] | None,
) -> dict[str, Any]:
    existing = dict(form_data or {})
    category_key = str(category or "").strip().lower()
    combined = " ".join(
        [
            str(description or ""),
            str(attachment_context.get("combined_text") or "") if attachment_context else "",
            " ".join(attachment_context.get("evidence_names") or []) if attachment_context else "",
        ]
    )
    text = re.sub(r"\s+", " ", combined)
    suggestions: dict[str, Any] = {}

    if not str(existing.get("key_dates") or "").strip():
        date_match = _pick_first(
            [
                r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
                r"\b(\d{1,2}\s+de\s+[a-zA-ZáéíóúÁÉÍÓÚ]+\s+de\s+\d{4})\b",
                r"\b([a-zA-ZáéíóúÁÉÍÓÚ]+\s+de\s+\d{4})\b",
            ],
            text,
        )
        if date_match:
            suggestions["key_dates"] = date_match

    if not str(existing.get("target_entity") or "").strip():
        entity_match = _pick_first(
            [
                r"\b(?:eps|ips|banco|entidad|empresa|colegio|universidad)\s+([A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ&.\- ]{2,60})",
                r"\b(Bancolombia|Davivienda|BBVA|Banco de Bogota|Banco Popular|Banco Caja Social|Nequi|Daviplata|Sura|Sanitas|Nueva EPS|Compensar|Coosalud|Claro|Movistar|Tigo)\b",
            ],
            text,
        )
        if entity_match:
            suggestions["target_entity"] = entity_match

    if not str(existing.get("evidence_summary") or "").strip():
        evidence_names = attachment_context.get("evidence_names") or [] if attachment_context else []
        if evidence_names:
            suggestions["evidence_summary"] = ", ".join(evidence_names[:5])

    if category_key == "bancos":
        if not str(existing.get("bank_product_type") or "").strip():
            product_match = _pick_first(
                [
                    r"\b(tarjeta de credito|tarjeta|cuenta de ahorros|cuenta corriente|prestamo|credito|seguro)\b",
                ],
                text,
            )
            if product_match:
                suggestions["bank_product_type"] = product_match
        if not str(existing.get("disputed_charge") or "").strip():
            charge_match = _pick_first(
                [
                    r"\b(seguro de [\w\s]+|cuota de manejo|interes de mora|cobro no autorizado|cargo no reconocido|reporte negativo|bloqueo)\b",
                ],
                text,
            )
            if charge_match:
                suggestions["disputed_charge"] = charge_match
        if not str(existing.get("bank_amount_involved") or "").strip():
            amount_match = _pick_first(
                [
                    r"(\$\s?\d[\d\.\,]{2,})",
                    r"(\d[\d\.\,]{3,}\s?(?:pesos|cop))",
                ],
                text,
            )
            if amount_match:
                suggestions["bank_amount_involved"] = amount_match
        if not str(existing.get("bank_event_date") or "").strip() and suggestions.get("key_dates"):
            suggestions["bank_event_date"] = suggestions["key_dates"]

    if category_key == "salud":
        if not str(existing.get("diagnosis") or "").strip():
            diagnosis_match = _pick_first(
                [
                    r"\bdiagnostico[:\s]+([A-ZÁÉÍÓÚÑa-záéíóúñ0-9 ,.\-]{5,80})",
                    r"\b(?:dx|diagnosis)[:\s]+([A-ZÁÉÍÓÚÑa-záéíóúñ0-9 ,.\-]{5,80})",
                ],
                text,
            )
            if diagnosis_match:
                suggestions["diagnosis"] = diagnosis_match
        if not str(existing.get("treatment_needed") or "").strip():
            treatment_match = _pick_first(
                [
                    r"\b(medicamento [A-ZÁÉÍÓÚÑa-záéíóúñ0-9 \-]{3,60})\b",
                    r"\b(cita con [A-ZÁÉÍÓÚÑa-záéíóúñ0-9 \-]{3,60})\b",
                    r"\b(procedimiento [A-ZÁÉÍÓÚÑa-záéíóúñ0-9 \-]{3,60})\b",
                ],
                text,
            )
            if treatment_match:
                suggestions["treatment_needed"] = treatment_match

    if category_key == "datos":
        if not str(existing.get("disputed_data") or "").strip():
            data_match = _pick_first(
                [
                    r"\b(reporte negativo [A-ZÁÉÍÓÚÑa-záéíóúñ0-9 \-]{0,60})\b",
                    r"\b(dato [A-ZÁÉÍÓÚÑa-záéíóúñ0-9 \-]{3,60})\b",
                ],
                text,
            )
            if data_match:
                suggestions["disputed_data"] = data_match

    return suggestions


def suggest_fields_from_context(
    *,
    category: str | None,
    description: str,
    form_data: dict[str, Any] | None,
    attachment_context: dict[str, Any] | None,
) -> dict[str, Any]:
    existing = dict(form_data or {})
    category_key = str(category or "").strip().lower()
    combined = " ".join(
        [
            str(description or ""),
            str(attachment_context.get("combined_text") or "") if attachment_context else "",
            " ".join(attachment_context.get("evidence_names") or []) if attachment_context else "",
        ]
    )
    text = re.sub(r"\s+", " ", combined)
    suggestions: dict[str, Any] = {}
    month_chars = "A-Za-zÁÉÍÓÚáéíóúÑñ"
    word_chars = "A-Za-zÁÉÍÓÚáéíóúÑñ"
    org_chars = "A-Za-zÁÉÍÓÚáéíóúÑñ&.\\-"

    if not str(existing.get("key_dates") or "").strip():
        date_match = _pick_first(
            [
                r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
                rf"\b(\d{{1,2}}\s+de\s+[{month_chars}]+\s+de\s+\d{{4}})\b",
                rf"\b([{month_chars}]+\s+de\s+\d{{4}})\b",
            ],
            text,
        )
        if date_match:
            suggestions["key_dates"] = date_match

    if not str(existing.get("target_entity") or "").strip():
        entity_match = _pick_first(
            [
                r"\b(Bancolombia|Davivienda|BBVA|Banco de Bogota|Banco Popular|Banco Caja Social|Nequi|Daviplata|Sura|Sanitas|Nueva EPS|Compensar|Coosalud|Claro|Movistar|Tigo)\b",
                rf"\b(?:eps|ips|banco|entidad|empresa|colegio|universidad)\s+([A-ZÁÉÍÓÚÑ][{org_chars}]{{2,30}}(?:\s+[A-ZÁÉÍÓÚÑ][{org_chars}]{{2,30}}){{0,3}})\b",
            ],
            text,
        )
        if entity_match:
            suggestions["target_entity"] = entity_match

    if not str(existing.get("evidence_summary") or "").strip():
        evidence_names = attachment_context.get("evidence_names") or [] if attachment_context else []
        if evidence_names:
            suggestions["evidence_summary"] = ", ".join(evidence_names[:5])

    if category_key == "bancos":
        if not str(existing.get("bank_product_type") or "").strip():
            product_match = _pick_first(
                [
                    r"\b(tarjeta de credito|tarjeta|cuenta de ahorros|cuenta corriente|prestamo|credito|seguro)\b",
                ],
                text,
            )
            if product_match:
                suggestions["bank_product_type"] = product_match
        if not str(existing.get("disputed_charge") or "").strip():
            charge_match = _pick_first(
                [
                    rf"\b(seguro de [{word_chars} ]{{3,40}}|cuota de manejo|interes de mora|cobro no autorizado|cargo no reconocido|reporte negativo|bloqueo)\b",
                ],
                text,
            )
            if charge_match:
                suggestions["disputed_charge"] = charge_match
        if not str(existing.get("bank_amount_involved") or "").strip():
            amount_match = _pick_first(
                [
                    r"(\$\s?\d[\d\.\,]{2,})",
                    r"(\d[\d\.\,]{3,}\s?(?:pesos|cop))",
                ],
                text,
            )
            if amount_match:
                suggestions["bank_amount_involved"] = amount_match
        if not str(existing.get("bank_event_date") or "").strip() and suggestions.get("key_dates"):
            suggestions["bank_event_date"] = suggestions["key_dates"]

    if category_key == "salud":
        if not str(existing.get("diagnosis") or "").strip():
            diagnosis_match = _pick_first(
                [
                    rf"\bdiagnostico[:\s]+([{word_chars}0-9 ,.\-]{{5,80}})",
                    rf"\b(?:dx|diagnosis)[:\s]+([{word_chars}0-9 ,.\-]{{5,80}})",
                ],
                text,
            )
            if diagnosis_match:
                suggestions["diagnosis"] = diagnosis_match
        if not str(existing.get("treatment_needed") or "").strip():
            treatment_match = _pick_first(
                [
                    rf"\b(medicamento [{word_chars}0-9 \-]{{3,60}})\b",
                    rf"\b(cita con [{word_chars}0-9 \-]{{3,60}})\b",
                    rf"\b(procedimiento [{word_chars}0-9 \-]{{3,60}})\b",
                ],
                text,
            )
            if treatment_match:
                suggestions["treatment_needed"] = treatment_match

    if category_key == "datos":
        if not str(existing.get("disputed_data") or "").strip():
            data_match = _pick_first(
                [
                    rf"\b(reporte negativo [{word_chars}0-9 \-]{{0,60}})\b",
                    rf"\b(dato [{word_chars}0-9 \-]{{3,60}})\b",
                ],
                text,
            )
            if data_match:
                suggestions["disputed_data"] = data_match

    return suggestions
