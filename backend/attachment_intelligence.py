from __future__ import annotations

import re
from pathlib import Path
from typing import Any

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
        for page in reader.pages[:4]:
            text = (page.extract_text() or "").strip()
            if text:
                chunks.append(text)
        return "\n".join(chunks)
    except Exception:
        return ""


def _read_docx(path: Path) -> str:
    if Document is None:
        return ""
    try:
        document = Document(str(path))
        parts = [(paragraph.text or "").strip() for paragraph in document.paragraphs[:60]]
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

    represented_person_name = _pick_first(
        [
            r"\b(?:nombre del paciente|paciente|nombre|nombres y apellidos)[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{5,80})",
        ],
        compact_text,
    )
    if represented_person_name:
        suggestions["represented_person_name"] = represented_person_name

    represented_person_document = _pick_first(
        [
            r"\b(?:tarjeta de identidad|ti|registro civil|nuip|identificacion|identificación)[:\s#-]*([0-9.\-]{6,20})",
        ],
        compact_text,
    )
    if represented_person_document:
        suggestions["represented_person_document"] = represented_person_document

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

    physician = _pick_first(
        [
            r"\b(?:medico tratante|médico tratante|hematologo|hematólogo|doctor|doctora|dr\.|dra\.)[:\s]+([A-Za-zÁÉÍÓÚáéíóúÑñ ]{5,80})",
        ],
        compact_text,
    )
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
            suggestions["treatment_needed"] = treatment_needed
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

    for item in file_records:
        text = extract_file_text(item)
        if text:
            compact = re.sub(r"\s+", " ", text).strip()
            if compact:
                file_name = str(item.get("original_name") or "").strip()
                profile = _extract_attachment_suggestions(file_name, compact)
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
                combined_text_parts.append(compact[:2500])
                extracted_chunks.append(f"Archivo {item.get('original_name')}: {compact[:500]}")

    combined_text = " ".join(combined_text_parts)
    lowered = combined_text.lower()
    clues: list[str] = []

    if any(term in lowered for term in ["registro civil", "tarjeta de identidad", "menor de edad", "acudiente", "madre del menor", "padre del menor"]):
        clues.append("Los anexos sugieren que el caso involucra a un menor de edad o persona representada.")
    if any(term in lowered for term in ["formula medica", "orden medica", "historia clinica", "diagnostico", "medicamento", "dosis"]):
        clues.append("Los anexos contienen informacion medica relevante sobre diagnostico, formula o tratamiento.")
    if any(term in lowered for term in ["eps", "autorizacion", "negado", "pendiente", "medicamentos"]):
        clues.append("Los anexos parecen mostrar relacion con EPS, autorizaciones o negacion de servicios de salud.")

    return {
        "evidence_names": evidence_names,
        "extracted_text_available": bool(combined_text_parts),
        "combined_text": combined_text[:12000],
        "summary_lines": extracted_chunks[:4],
        "clues": clues,
        "attachment_profiles": attachment_profiles[:6],
        "typed_suggestions": typed_suggestions,
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
