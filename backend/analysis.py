from __future__ import annotations

from typing import Any

from backend import repository


def summarize_action(strategy: str, legal_analysis: dict[str, Any]) -> str:
    action = legal_analysis.get("recommended_action")
    if isinstance(action, str) and action.strip():
        return action.strip()

    normalized = strategy.lower()
    if "tutela" in normalized:
        return "Acción de tutela"
    if "petición" in normalized or "peticion" in normalized:
        return "Derecho de petición"
    if "desacato" in normalized:
        return "Incidente de desacato"
    return "Solicitud jurídica"


def build_routing(category: str, city: str, department: str, fact_data: dict[str, Any]) -> dict[str, Any]:
    entities = fact_data.get("entidades_involucradas") or fact_data.get("entities") or []
    entity_names = [str(item).strip() for item in entities if str(item).strip()]

    court = repository.search_best_court(city, department)
    entity_matches = repository.search_entities(category, entity_names)

    primary_target = None
    if court:
        primary_target = {
            "type": "juzgado",
            "name": court.get("tipo_oficina") or court.get("municipio") or "Rama Judicial",
            "channel": "portal/email",
            "contact": court.get("correo_reparto") or court.get("url_referencia"),
            "reason": "Canal sugerido para radicar tutela según ciudad/departamento.",
            "metadata": {
                "municipio": court.get("municipio"),
                "departamento": court.get("departamento"),
                "codigo": court.get("codigo_interno"),
                "plataforma": court.get("plataforma_oficial"),
            },
        }

    secondary_targets = [
        {
            "type": "entidad",
            "name": match.get("nombre_entidad"),
            "channel": match.get("canal_envio"),
            "contact": match.get("contacto_envio"),
            "reason": "Entidad relacionada detectada en la base de datos operativa.",
            "metadata": {
                "modulo": match.get("modulo"),
                "paso_flujo": match.get("paso_flujo"),
                "plazo_respuesta": match.get("plazo_respuesta"),
            },
        }
        for match in entity_matches
    ]

    return {
        "primary_target": primary_target,
        "secondary_targets": secondary_targets,
        "city": city,
        "department": department,
        "detected_entities": entity_names,
    }


def build_document(case: dict[str, Any]) -> str:
    recommended_action = case.get("recommended_action") or "Acción jurídica"
    facts = case.get("facts") or {}
    legal_analysis = case.get("legal_analysis") or {}
    routing = case.get("routing") or {}
    rights = legal_analysis.get("derechos_vulnerados") or legal_analysis.get("rights_violated") or []
    rules = legal_analysis.get("normas_relevantes") or legal_analysis.get("relevant_rules") or []

    facts_summary = facts.get("hechos_principales") or facts.get("summary") or case.get("description") or ""
    rights_text = ", ".join(rights) if isinstance(rights, list) else str(rights)
    rules_text = ", ".join(rules) if isinstance(rules, list) else str(rules)
    target = (routing.get("primary_target") or {}).get("name") or "la autoridad competente"

    return f"""Señores
{target}

Referencia: {recommended_action}

Yo, {case.get('user_name')}, identificado(a) con el correo {case.get('user_email')}, residente en {case.get('user_city')}, {case.get('user_department')}, presento esta solicitud por la vulneración de mis derechos.

Hechos relevantes:
{facts_summary}

Derechos comprometidos:
{rights_text or 'Derechos fundamentales identificados durante el análisis del caso.'}

Fundamento jurídico:
{rules_text or case.get('strategy_text')}

Pretensiones sugeridas:
1. Que se adopten medidas inmediatas para proteger mis derechos.
2. Que se dé respuesta de fondo dentro de los términos legales.
3. Que se remita constancia de radicación o de la actuación adelantada.

Observaciones de la app:
{case.get('strategy_text')}

Atentamente,
{case.get('user_name')}
Correo: {case.get('user_email')}
"""
