from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import repository_ext as repository
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
        if "Automatización" in sheet_name or "Automatizaci" in sheet_name:
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
        if "DEPARTAMENTO" in values and ("CÓDIGO" in values or "CÃ“DIGO" in values):
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


def _seed_business_rules_from_workbook(path: str) -> None:
    workbook = pd.ExcelFile(path)
    rules_sheet = pd.read_excel(path, sheet_name=workbook.sheet_names[0], header=None).fillna("")
    current_rule_key = None
    current_payload: dict[str, Any] = {}
    rule_counter = 0

    for _, row in rules_sheet.iterrows():
        left = str(row.iloc[0]).strip()
        right = str(row.iloc[1]).strip() if len(row) > 1 else ""
        normalized = left.upper()
        if normalized.startswith("REGLA "):
            if current_rule_key:
                repository.upsert_business_rule(**current_payload)
            rule_counter += 1
            current_rule_key = f"rule-{rule_counter}"
            current_payload = {
                "rule_key": current_rule_key,
                "title": left,
                "description": "",
                "action_text": "",
                "priority": None,
                "metadata": {"source_sheet": workbook.sheet_names[0]},
            }
            continue

        if not current_rule_key or not left:
            continue

        if normalized in {"QUÉ APLICA", "QUE APLICA", "REGLA", "POR QUÉ", "POR QUE", "IMPLEMENTACIÓN", "IMPLEMENTACION", "DATO REQUERIDO", "FLUJO (PASO A PASO)", "APRENDIZAJE"}:
            current_payload["metadata"][left] = right
            if normalized in {"REGLA", "FLUJO (PASO A PASO)"} and right:
                current_payload["description"] = right
            if normalized in {"IMPLEMENTACIÓN", "IMPLEMENTACION"} and right:
                current_payload["action_text"] = right
    if current_rule_key:
        repository.upsert_business_rule(**current_payload)

    tree_sheet = pd.read_excel(path, sheet_name=workbook.sheet_names[1]).fillna("")
    for _, row in tree_sheet.iterrows():
        step = str(row.get("PASO", "")).strip()
        question = str(row.get("PREGUNTA / ACCIÓN", row.get("PREGUNTA / ACCIÃ“N", ""))).strip()
        result = str(row.get("RESULTADO / ACCIÓN APP", row.get("RESULTADO / ACCIÃ“N APP", ""))).strip()
        next_step = str(row.get("SIGUIENTE PASO", "")).strip()
        if not step or not question:
            continue
        repository.upsert_business_rule(
            rule_key=f"decision-step-{step}",
            title=f"Árbol de decisión paso {step}",
            description=question,
            action_text=result,
            priority=None,
            metadata={"next_step": next_step, "source_sheet": workbook.sheet_names[1]},
        )

    repository.upsert_business_rule(
        rule_key="rule-copy-user",
        title="Siempre enviar copia al usuario",
        description="En todos los casos el comprobante o envío debe copiar al correo del usuario.",
        action_text="Agregar siempre el correo del usuario en CC y conservar soporte del envío.",
        priority="ALTA",
        metadata={"source": "normalized"},
    )
    repository.upsert_business_rule(
        rule_key="rule-missing-channel",
        title="Entidad sin canal digital verificado",
        description="Si la entidad no tiene canal digital, primero pedir contacto al usuario y luego activar modo presencial si sigue faltando información.",
        action_text="Solicitar correo o dirección al usuario y guardar el dato para futuros casos.",
        priority="ALTA",
        metadata={"source": "normalized"},
    )


def _seed_legacy_business_rules(path: str) -> None:
    rules = json.loads(Path(path).read_text(encoding="utf-8"))
    for index, rule in enumerate(rules, start=1):
        repository.upsert_business_rule(
            rule_key=f"legacy-business-rule-{index}",
            title=rule.get("Regla", f"Regla {index}"),
            description=rule.get("Descripción", rule.get("DescripciÃ³n", "")),
            action_text=rule.get("Acción", rule.get("AcciÃ³n")),
            priority=rule.get("Prioridad"),
            metadata={"source": "legacy_json"},
        )


def seed_all() -> None:
    _load_entity_sheets("BD_Entidades_Destino_Defiendo_Colombia.xlsx")
    _load_courts("BD_Juzgados_Tutelas_Colombia_DefiendeApp.xlsx")
    _seed_knowledge(settings.knowledge_base_json)
    _seed_business_rules_from_workbook("BD_Reglas_Envio_Defiendo_Colombia (1).xlsx")
    _seed_legacy_business_rules("execution/business_rules.json")
    print("Datos de referencia v2 cargados correctamente.")


if __name__ == "__main__":
    seed_all()
