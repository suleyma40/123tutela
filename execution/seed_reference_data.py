from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import repository
from backend.config import settings


def _clean(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _load_entity_sheets(path: str) -> None:
    workbook = pd.ExcelFile(path)
    for sheet_name in workbook.sheet_names:
        if "Automatización" in sheet_name:
            continue

        frame = pd.read_excel(path, sheet_name=sheet_name)
        frame.columns = range(len(frame.columns))

        header_index = None
        for index, row in frame.iterrows():
            values = [str(value).upper() for value in row.values if not pd.isna(value)]
            if "ENTIDAD DESTINO" in values:
                header_index = index
                break

        if header_index is None:
            continue

        for _, row in frame.iloc[header_index + 1 :].iterrows():
            nombre_entidad = _clean(row[2] if len(row) > 2 else None)
            if not nombre_entidad:
                continue

            repository.upsert_entity(
                {
                    "modulo": _clean(row[0] if len(row) > 0 else None),
                    "paso_flujo": _clean(row[1] if len(row) > 1 else None),
                    "nombre_entidad": nombre_entidad,
                    "canal_envio": _clean(row[3] if len(row) > 3 else None),
                    "contacto_envio": _clean(row[4] if len(row) > 4 else None),
                    "genera_radicado": str(_clean(row[5] if len(row) > 5 else "")).lower() in {"si", "sí", "true", "1", "✅"},
                    "plazo_respuesta": _clean(row[6] if len(row) > 6 else None),
                    "observaciones": _clean(row[7] if len(row) > 7 else None),
                    "automatizable": str(_clean(row[8] if len(row) > 8 else "")).lower() in {"si", "sí", "true", "1", "✅"},
                    "prioridad": int(row[9]) if len(row) > 9 and str(row[9]).isdigit() else 1,
                }
            )


def _load_courts(path: str) -> None:
    frame = pd.read_excel(path, sheet_name="BASE JUZGADOS")
    frame.columns = range(len(frame.columns))

    header_index = None
    for index, row in frame.iterrows():
        values = [str(value).upper() for value in row.values if not pd.isna(value)]
        if "DEPARTAMENTO" in values and "CÓDIGO" in values:
            header_index = index
            break

    if header_index is None:
        return

    for _, row in frame.iloc[header_index + 1 :].iterrows():
        codigo = _clean(row[10] if len(row) > 10 else None)
        correo = _clean(row[4] if len(row) > 4 else None)
        if not codigo or not correo:
            continue

        repository.upsert_court(
            {
                "departamento": _clean(row[1] if len(row) > 1 else None),
                "municipio": _clean(row[2] if len(row) > 2 else None),
                "tipo_oficina": _clean(row[3] if len(row) > 3 else None),
                "correo_reparto": correo,
                "correo_alternativo": _clean(row[5] if len(row) > 5 else None),
                "tipo_tutela": _clean(row[6] if len(row) > 6 else None),
                "asunto_recomendado": _clean(row[7] if len(row) > 7 else None),
                "plataforma_oficial": _clean(row[8] if len(row) > 8 else None),
                "url_referencia": _clean(row[9] if len(row) > 9 else None),
                "codigo_interno": codigo,
                "prioridad": _clean(row[11] if len(row) > 11 else None),
                "notas": _clean(row[12] if len(row) > 12 else None),
            }
        )


def _seed_knowledge(path: str) -> None:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    for key, content in payload.items():
        title = key.replace("_", " ").title()
        tags = [segment for segment in key.split("_") if segment]
        repository.upsert_knowledge_item(key, title, content, "knowledge_base_json", tags)


def _seed_business_rules(path: str) -> None:
    rules = json.loads(Path(path).read_text(encoding="utf-8"))
    for index, rule in enumerate(rules, start=1):
        repository.upsert_business_rule(
            rule_key=f"business-rule-{index}",
            title=rule.get("Regla", f"Regla {index}"),
            description=rule.get("Descripción", ""),
            action_text=rule.get("Acción"),
            priority=rule.get("Prioridad"),
        )


def seed_all() -> None:
    _load_entity_sheets("BD_Entidades_Destino_Defiendo_Colombia.xlsx")
    _load_courts("BD_Juzgados_Tutelas_Colombia_DefiendeApp.xlsx")
    _seed_knowledge(settings.knowledge_base_json)
    _seed_business_rules("execution/business_rules.json")
    print("Datos de referencia cargados correctamente.")


if __name__ == "__main__":
    seed_all()
