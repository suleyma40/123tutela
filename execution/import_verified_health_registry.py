from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOWNLOAD_FILE = Path.home() / "Downloads" / "jurisprudencia-salud-verificada.js"
REGISTRY_FILE = ROOT / "knowledge_base" / "verified_legal_registry.json"

APPROVED_DOMAINS = {
    "www.corteconstitucional.gov.co",
    "corteconstitucional.gov.co",
    "www.consejodeestado.gov.co",
    "consejodeestado.gov.co",
    "www.vlex.com.co",
    "vlex.com.co",
}

CATEGORY_USAGE = {
    "principios_fundamentales": ["salud", "tutela_salud", "peticion_salud"],
    "medicamentos_procedimientos": ["salud", "tutela_salud"],
    "tutela_salud_procedencia": ["salud", "tutela_salud", "impugnacion_salud"],
    "pqrs_peticion_salud": ["salud", "peticion_salud", "tutela_salud"],
    "desacato_salud": ["salud", "desacato_salud", "impugnacion_salud"],
}


def _slug_case_number(numero: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", numero.lower()).strip("_")


def _official_corte_url(numero: str) -> str:
    match = re.fullmatch(r"([A-Z]+)-(\d+[A-Z]?)/(\d{4})", numero.strip(), flags=re.I)
    if not match:
        return ""
    prefix, seq, year = match.groups()
    prefix = prefix.lower()
    seq = seq.lower()
    short_year = year[-2:]
    if prefix == "su":
        return f"https://www.corteconstitucional.gov.co/relatoria/{year}/su{seq}-{short_year}.htm"
    return f"https://www.corteconstitucional.gov.co/relatoria/{year}/{prefix}-{seq}-{short_year}.htm"


def _approved_url(numero: str, raw_url: str) -> str:
    url = str(raw_url or "").strip()
    if any(domain in url.lower() for domain in APPROVED_DOMAINS):
        return url
    fallback = _official_corte_url(numero)
    return fallback or url


def _field(block: str, name: str) -> str:
    match = re.search(rf"{name}:\s*'([^']*)'", block, flags=re.S)
    return match.group(1).strip() if match else ""


def _aliases(numero: str, tema: str) -> list[str]:
    numero = numero.strip()
    lowered = numero.lower()
    year_style = re.sub(r"/(\d{4})$", r" de \1", lowered)
    base = [
        numero,
        lowered,
        f"sentencia {numero}",
        f"sentencia {lowered}",
        year_style,
        f"sentencia {year_style}",
    ]
    if tema:
        base.append(tema)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in base:
        clean = str(item or "").strip()
        if not clean or clean.lower() in seen:
            continue
        seen.add(clean.lower())
        deduped.append(clean)
    return deduped


def _load_js_text() -> str:
    text = DOWNLOAD_FILE.read_text(encoding="utf-8", errors="replace")
    return text


def _parse_health_cases(text: str) -> list[tuple[str, dict[str, str]]]:
    categories = re.findall(r"^\s*([a-z_]+):\s*\{", text, flags=re.M)
    records: list[tuple[str, dict[str, str]]] = []
    for category in categories:
        category_start = text.find(f"{category}:")
        if category_start < 0:
            continue
        next_positions = [text.find(f"{name}:", category_start + 1) for name in categories if text.find(f"{name}:", category_start + 1) > category_start]
        category_end = min(next_positions) if next_positions else len(text)
        block = text[category_start:category_end]
        for sentence_block in re.findall(r"\{\s*numero:\s*'[^']+'.*?verificada:\s*true,?\s*(?:nota:\s*'[^']*',?\s*)?\}", block, flags=re.S):
            numero = _field(sentence_block, "numero")
            if not numero:
                continue
            records.append(
                (
                    category,
                    {
                        "numero": numero,
                        "magistrado": _field(sentence_block, "magistrado"),
                        "fecha": _field(sentence_block, "fecha"),
                        "tema": _field(sentence_block, "tema"),
                        "resumen": _field(sentence_block, "resumen"),
                        "cita": _field(sentence_block, "cita"),
                        "cuando_usar": _field(sentence_block, "cuando_usar"),
                        "url": _field(sentence_block, "url"),
                    },
                )
            )
    return records


def main() -> None:
    if not DOWNLOAD_FILE.exists():
        raise SystemExit(f"No existe el archivo fuente: {DOWNLOAD_FILE}")

    text = _load_js_text()
    parsed = _parse_health_cases(text)
    if not parsed:
        raise SystemExit("No se pudieron extraer sentencias del archivo descargado.")

    payload = json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    sources = dict(payload.get("sources") or {})

    imported = 0
    for category, item in parsed:
        numero = item["numero"]
        key = f"salud_{category}_{_slug_case_number(numero)}"
        url = _approved_url(numero, item["url"])
        source = {
            "aliases": _aliases(numero, item["tema"]),
            "tipo_fuente": "jurisprudencia",
            "corporacion": "Corte Constitucional",
            "numero_sentencia_o_norma": f"Sentencia {numero.replace('/', ' de ')}",
            "fecha": item["fecha"] or None,
            "url_verificada": url,
            "extracto_relevante": item["cita"] or item["resumen"] or item["cuando_usar"] or f"Precedente de salud {numero}.",
            "tema_juridico": item["tema"] or f"salud - {category}",
            "nivel_confiabilidad": "alto",
            "source_level": 1,
            "uso": CATEGORY_USAGE.get(category, ["salud"]),
        }
        sources[key] = source
        imported += 1

    payload["metadata"]["last_updated"] = "2026-03-18"
    notes = list(payload["metadata"].get("notes") or [])
    import_note = "La jurisprudencia de salud se importa desde jurisprudencia-salud-verificada.js descargado y se normaliza contra dominios permitidos."
    if import_note not in notes:
        notes.append(import_note)
    payload["metadata"]["notes"] = notes
    payload["sources"] = sources
    REGISTRY_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Imported {imported} health precedents into {REGISTRY_FILE}")


if __name__ == "__main__":
    main()
