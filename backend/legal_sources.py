from __future__ import annotations

from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


VERIFIED_SOURCE_REGISTRY: dict[str, dict[str, Any]] = {
    "constitucion_art_86": {
        "aliases": [
            "constitucion politica de 1991, articulo 86",
            "constitucion politica art. 86",
            "constitucion politica art 86",
            "articulo 86 cp",
            "accion de tutela",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Constitucion Politica de Colombia",
        "numero_sentencia_o_norma": "Articulo 86",
        "fecha": "1991-07-04",
        "url_verificada": "https://www.suin-juriscol.gov.co/legislacion/accionesconstitucionales.html",
        "extracto_relevante": "Consagra la accion de tutela para la proteccion inmediata de derechos fundamentales.",
        "tema_juridico": "accion de tutela",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["tutela", "impugnacion", "desacato"],
    },
    "decreto_2591_art_14": {
        "aliases": [
            "decreto 2591 de 1991",
            "decreto 2591 de 1991 articulo 14",
            "decreto 2591/1991 art. 14",
            "contenido e informalidad de la solicitud de tutela",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Presidencia de la Republica / SUIN-Juriscol",
        "numero_sentencia_o_norma": "Decreto 2591 de 1991, articulo 14",
        "fecha": "1991-11-19",
        "url_verificada": "https://www.suin-juriscol.gov.co/viewDocument.asp?id=1470723",
        "extracto_relevante": "Regula el contenido minimo e informalidad de la solicitud de tutela.",
        "tema_juridico": "contenido de la tutela",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["tutela"],
    },
    "decreto_2591_art_52": {
        "aliases": [
            "decreto 2591/1991 art. 52",
            "decreto 2591 de 1991 articulo 52",
            "incidente de desacato",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Presidencia de la Republica / SUIN-Juriscol",
        "numero_sentencia_o_norma": "Decreto 2591 de 1991, articulo 52",
        "fecha": "1991-11-19",
        "url_verificada": "https://www.suin-juriscol.gov.co/viewDocument.asp?id=1470723",
        "extracto_relevante": "Regula el incidente de desacato por incumplimiento de fallos de tutela.",
        "tema_juridico": "desacato",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["desacato"],
    },
    "derecho_peticion_suin": {
        "aliases": [
            "ley 1755 de 2015",
            "derecho de peticion",
            "derecho de petición",
            "articulo 23 cp",
            "ley 1755",
        ],
        "tipo_fuente": "norma",
        "corporacion": "SUIN-Juriscol",
        "numero_sentencia_o_norma": "Regimen de derecho de peticion",
        "fecha": "2015-06-30",
        "url_verificada": "https://www.suin-juriscol.gov.co/legislacion/derechodepeticion.html",
        "extracto_relevante": "Compila objeto, modalidades, contenido y terminos del derecho de peticion.",
        "tema_juridico": "derecho de peticion",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["peticion", "reclamacion", "tutela_por_silencio"],
    },
    "funcion_publica_peticion_1": {
        "aliases": [
            "terminos de respuesta derecho de peticion",
            "respuesta de fondo peticion",
        ],
        "tipo_fuente": "guia_institucional",
        "corporacion": "Funcion Publica",
        "numero_sentencia_o_norma": "Concepto / gestor normativo 170948",
        "fecha": None,
        "url_verificada": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=170948",
        "extracto_relevante": "Referencia administrativa sobre terminos y contenido de la peticion.",
        "tema_juridico": "terminos de respuesta",
        "nivel_confiabilidad": "medio",
        "source_level": 2,
        "uso": ["peticion"],
    },
    "funcion_publica_peticion_2": {
        "aliases": [
            "contenido derecho de peticion",
            "peticion clara y congruente",
        ],
        "tipo_fuente": "guia_institucional",
        "corporacion": "Funcion Publica",
        "numero_sentencia_o_norma": "Concepto / gestor normativo 266477",
        "fecha": None,
        "url_verificada": "https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=266477",
        "extracto_relevante": "Guia institucional sobre respuesta de fondo y alcance del derecho de peticion.",
        "tema_juridico": "contenido de respuesta",
        "nivel_confiabilidad": "medio",
        "source_level": 2,
        "uso": ["peticion"],
    },
}


ACTION_SOURCE_KEYS: dict[str, list[str]] = {
    "accion de tutela": ["constitucion_art_86", "decreto_2591_art_14"],
    "accion de tutela por habeas data": ["constitucion_art_86", "decreto_2591_art_14"],
    "impugnacion de tutela": ["constitucion_art_86", "decreto_2591_art_14"],
    "incidente de desacato": ["constitucion_art_86", "decreto_2591_art_52"],
    "derecho de peticion": ["derecho_peticion_suin", "funcion_publica_peticion_1", "funcion_publica_peticion_2"],
    "derecho de peticion financiero": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "derecho de peticion a eps": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "derecho de peticion laboral": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "derecho de peticion al proveedor": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "derecho de peticion a empresa de servicios": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "reclamacion financiera": ["derecho_peticion_suin"],
    "reclamo administrativo": ["derecho_peticion_suin"],
    "reclamo de consumo": ["derecho_peticion_suin"],
    "reclamacion por servicios publicos": ["derecho_peticion_suin"],
    "reclamacion de habeas data": ["derecho_peticion_suin"],
}


def _normalize_source_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "tipo_fuente": record["tipo_fuente"],
        "corporacion": record["corporacion"],
        "numero_sentencia_o_norma": record["numero_sentencia_o_norma"],
        "fecha": record["fecha"],
        "url_verificada": record["url_verificada"],
        "extracto_relevante": record["extracto_relevante"],
        "tema_juridico": record["tema_juridico"],
        "nivel_confiabilidad": record["nivel_confiabilidad"],
        "source_level": record["source_level"],
    }


def _match_registry_entry(reference: str) -> dict[str, Any] | None:
    normalized = _lower(reference)
    for entry in VERIFIED_SOURCE_REGISTRY.values():
        aliases = [_lower(item) for item in entry.get("aliases", [])]
        if any(alias and alias in normalized for alias in aliases):
            return entry
    return None


def resolve_verified_legal_support(
    *,
    recommended_action: str | None,
    workflow_type: str | None,
    category: str | None,
    legal_analysis: dict[str, Any],
) -> dict[str, Any]:
    action_key = _lower(recommended_action)
    verified_sources: list[dict[str, Any]] = []
    warnings: list[str] = []
    verified_normas: list[str] = []
    verified_precedents: list[str] = []
    unresolved_precedents: list[str] = []
    unresolved_normas: list[str] = []

    desired_keys = list(ACTION_SOURCE_KEYS.get(action_key, []))
    if not desired_keys:
        if workflow_type == "tutela":
            desired_keys.extend(ACTION_SOURCE_KEYS["accion de tutela"])
        elif "peticion" in action_key:
            desired_keys.extend(ACTION_SOURCE_KEYS["derecho de peticion"])

    for key in desired_keys:
        entry = VERIFIED_SOURCE_REGISTRY.get(key)
        if entry:
            verified_sources.append(_normalize_source_record(entry))
            verified_normas.append(entry["numero_sentencia_o_norma"])

    for norma in legal_analysis.get("normas_relevantes") or []:
        entry = _match_registry_entry(str(norma))
        if entry:
            normalized = _normalize_source_record(entry)
            if normalized not in verified_sources:
                verified_sources.append(normalized)
            if entry["numero_sentencia_o_norma"] not in verified_normas:
                verified_normas.append(entry["numero_sentencia_o_norma"])
        else:
            unresolved_normas.append(str(norma))

    for precedent in legal_analysis.get("precedentes_jurisprudenciales") or []:
        entry = _match_registry_entry(str(precedent))
        if entry and entry["tipo_fuente"] == "jurisprudencia":
            normalized = _normalize_source_record(entry)
            if normalized not in verified_sources:
                verified_sources.append(normalized)
            verified_precedents.append(entry["numero_sentencia_o_norma"])
        else:
            unresolved_precedents.append(str(precedent))

    if unresolved_precedents:
        warnings.append(
            "No se encontro soporte jurisprudencial suficientemente verificable para: "
            + ", ".join(unresolved_precedents[:3])
            + ". Se recomienda revision humana o ampliar la busqueda."
        )
    if unresolved_normas and not verified_normas:
        warnings.append(
            "El caso contiene referencias normativas no verificadas automaticamente. "
            "El documento se apoyara solo en fuentes oficiales o verificadas disponibles."
        )
    if not verified_sources:
        warnings.append(
            "No se encontraron fuentes juridicas verificadas suficientes para este punto; "
            "se recomienda revision humana o ampliar la base oficial."
        )

    return {
        "verified_sources": verified_sources,
        "verified_normas": verified_normas,
        "verified_precedents": verified_precedents,
        "unresolved_normas": unresolved_normas,
        "unresolved_precedents": unresolved_precedents,
        "warnings": warnings,
        "research_status": "completed" if verified_sources else "insufficient_verified_support",
        "action_key": action_key or _lower(category),
    }


def build_verified_legal_basis_text(source_validation_policy: dict[str, Any]) -> str:
    verified_sources = source_validation_policy.get("verified_sources") or []
    if not verified_sources:
        return (
            "No se encontro soporte juridico suficientemente verificable para profundizar en citas especificas. "
            "El documento conserva un fundamento normativo conservador y puede requerir revision humana."
        )

    primary = [item for item in verified_sources if item.get("source_level") == 1]
    if not primary:
        primary = verified_sources

    fragments = [
        f"{item['numero_sentencia_o_norma']} ({item['corporacion']})"
        for item in primary[:3]
        if item.get("numero_sentencia_o_norma") and item.get("corporacion")
    ]
    if not fragments:
        return "El documento se apoya en fuentes oficiales verificadas disponibles para este tipo de actuacion."
    return "El sustento juridico verificado para este documento se apoya en " + ", ".join(fragments) + "."


def sanitize_legal_analysis(
    *,
    legal_analysis: dict[str, Any],
    source_validation_policy: dict[str, Any],
) -> dict[str, Any]:
    sanitized = dict(legal_analysis or {})
    sanitized["normas_verificadas"] = source_validation_policy.get("verified_normas") or []
    sanitized["precedentes_verificados"] = source_validation_policy.get("verified_precedents") or []
    if sanitized.get("precedentes_jurisprudenciales") and not sanitized["precedentes_verificados"]:
        sanitized["precedentes_jurisprudenciales"] = []
    if sanitized.get("normas_verificantes") is not None:
        sanitized.pop("normas_verificantes", None)
    return sanitized

