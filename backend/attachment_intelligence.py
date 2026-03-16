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


def build_attachment_context(file_records: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_names = [str(item.get("original_name") or "").strip() for item in file_records if item.get("original_name")]
    extracted_chunks: list[str] = []
    combined_text_parts: list[str] = []

    for item in file_records:
        text = extract_file_text(item)
        if text:
            compact = re.sub(r"\s+", " ", text).strip()
            if compact:
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
        "summary_lines": extracted_chunks[:4],
        "clues": clues,
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
