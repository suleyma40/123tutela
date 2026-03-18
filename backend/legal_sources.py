from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower()


def _compact_reference(value: Any) -> str:
    text = _lower(value)
    text = re.sub(r"\bsentencia\b", "", text)
    text = re.sub(r"\bde\s+\d{4}\b", "", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text.strip()


PRIMARY_JURISPRUDENCE_DOMAINS = {
    "www.corteconstitucional.gov.co",
    "corteconstitucional.gov.co",
    "www.consejodeestado.gov.co",
    "consejodeestado.gov.co",
}

SECONDARY_JURISPRUDENCE_DOMAINS = {
    "www.vlex.com.co",
    "vlex.com.co",
}


def _domain_from_url(value: Any) -> str:
    url = _text(value)
    if not url:
        return ""
    try:
        return (urlparse(url).netloc or "").lower().strip()
    except Exception:
        return ""


def _jurisprudence_source_tier(record: dict[str, Any]) -> int:
    if str(record.get("tipo_fuente") or "") != "jurisprudencia":
        return 1
    domain = _domain_from_url(record.get("url_verificada"))
    if domain in PRIMARY_JURISPRUDENCE_DOMAINS:
        return 1
    if domain in SECONDARY_JURISPRUDENCE_DOMAINS:
        return 2
    return 99


VERIFIED_SOURCE_REGISTRY: dict[str, dict[str, Any]] = {
    "constitucion_art_15": {
        "aliases": [
            "constitucion politica de 1991, articulo 15",
            "constitucion politica art. 15",
            "constitucion politica art 15",
            "articulo 15 cp",
            "habeas data",
            "buen nombre",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Constitucion Politica de Colombia",
        "numero_sentencia_o_norma": "Articulo 15",
        "fecha": "1991-07-04",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/constitucion_politica_1991.html",
        "extracto_relevante": "Reconoce el derecho a conocer, actualizar y rectificar informaciones recogidas en bancos de datos y archivos de entidades publicas y privadas.",
        "tema_juridico": "habeas data y buen nombre",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["habeas_data", "tutela", "reclamacion"],
    },
    "constitucion_art_23": {
        "aliases": [
            "constitucion politica de 1991, articulo 23",
            "constitucion politica art. 23",
            "constitucion politica art 23",
            "articulo 23 cp",
            "derecho de peticion",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Constitucion Politica de Colombia",
        "numero_sentencia_o_norma": "Articulo 23",
        "fecha": "1991-07-04",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/constitucion_politica_1991.html",
        "extracto_relevante": "Toda persona tiene derecho a presentar peticiones respetuosas y a obtener pronta resolucion.",
        "tema_juridico": "derecho de peticion",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["peticion", "tutela_por_silencio", "reclamacion"],
    },
    "constitucion_art_13": {
        "aliases": [
            "constitucion politica de 1991, articulo 13",
            "constitucion politica art. 13",
            "constitucion politica art 13",
            "articulo 13 cp",
            "igualdad ante la ley",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Constitucion Politica de Colombia",
        "numero_sentencia_o_norma": "Articulo 13",
        "fecha": "1991-07-04",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/constitucion_politica_1991.html",
        "extracto_relevante": "Reconoce el derecho a la igualdad y exige que las autoridades y particulares no impongan tratos discriminatorios o arbitrarios.",
        "tema_juridico": "igualdad y no discriminacion",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["reclamacion", "tutela", "consumo"],
    },
    "constitucion_art_78": {
        "aliases": [
            "constitucion politica de 1991, articulo 78",
            "constitucion politica art. 78",
            "constitucion politica art 78",
            "articulo 78 cp",
            "proteccion al consumidor",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Constitucion Politica de Colombia",
        "numero_sentencia_o_norma": "Articulo 78",
        "fecha": "1991-07-04",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/constitucion_politica_1991.html",
        "extracto_relevante": "Ordena la proteccion de consumidores y usuarios frente a la calidad, informacion y seguridad de bienes y servicios ofrecidos a la comunidad.",
        "tema_juridico": "proteccion al consumidor",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["reclamacion", "consumo", "financiero"],
    },
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
    "constitucion_art_49": {
        "aliases": [
            "constitucion politica de 1991, articulo 49",
            "constitucion politica art. 49",
            "constitucion politica art 49",
            "articulo 49 cp",
            "derecho a la salud",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Constitucion Politica de Colombia",
        "numero_sentencia_o_norma": "Articulo 49",
        "fecha": "2009-12-21",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/acto_legislativo_02_2009.html",
        "extracto_relevante": "Garantiza el acceso a los servicios de promocion, proteccion y recuperacion de la salud y fija su prestacion como servicio publico a cargo del Estado.",
        "tema_juridico": "salud",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["tutela_salud", "peticion_salud"],
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
    "decreto_2591_art_42": {
        "aliases": [
            "decreto 2591 de 1991 articulo 42",
            "decreto 2591/1991 art. 42",
            "tutela contra particular",
            "articulo 42 decreto 2591",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Presidencia de la Republica / SUIN-Juriscol",
        "numero_sentencia_o_norma": "Decreto 2591 de 1991, articulo 42",
        "fecha": "1991-11-19",
        "url_verificada": "https://www.suin-juriscol.gov.co/viewDocument.asp?id=1470723",
        "extracto_relevante": "Regula los eventos en los que la tutela procede contra particulares.",
        "tema_juridico": "tutela contra particulares",
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
    "ley_1751_2015": {
        "aliases": [
            "ley 1751 de 2015",
            "ley estatutaria 1751 de 2015",
            "derecho fundamental a la salud",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Congreso de la Republica",
        "numero_sentencia_o_norma": "Ley Estatutaria 1751 de 2015",
        "fecha": "2015-02-16",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/ley_1751_2015.html",
        "extracto_relevante": "Regula el derecho fundamental a la salud, su caracter autonomo e irrenunciable y los mecanismos para su garantia.",
        "tema_juridico": "salud",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["tutela_salud", "peticion_salud"],
    },
    "ley_1755_2015": {
        "aliases": [
            "ley 1755 de 2015",
            "regimen de derecho de peticion",
            "derecho de peticion ley 1755",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Congreso de la Republica",
        "numero_sentencia_o_norma": "Ley 1755 de 2015",
        "fecha": "2015-06-30",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/ley_1755_2015.html",
        "extracto_relevante": "Regula el derecho fundamental de peticion, sus modalidades, contenido y terminos de respuesta ante autoridades y particulares obligados.",
        "tema_juridico": "derecho de peticion",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["peticion", "tutela_por_silencio", "reclamacion"],
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
    "ley_1266_2008": {
        "aliases": [
            "ley 1266 de 2008",
            "habeas data financiero",
            "reporte en centrales de riesgo",
            "dato financiero",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Congreso de la Republica",
        "numero_sentencia_o_norma": "Ley 1266 de 2008",
        "fecha": "2008-12-31",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/ley_1266_2008.html",
        "extracto_relevante": "Desarrolla el habeas data financiero y regula la administracion de informacion financiera, crediticia, comercial y de servicios.",
        "tema_juridico": "habeas data financiero",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["habeas_data", "financiero", "reclamacion"],
    },
    "ley_1328_2009": {
        "aliases": [
            "ley 1328 de 2009",
            "consumidor financiero",
            "proteccion al consumidor financiero",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Congreso de la Republica",
        "numero_sentencia_o_norma": "Ley 1328 de 2009",
        "fecha": "2009-07-15",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/ley_1328_2009.html",
        "extracto_relevante": "Establece el regimen de proteccion al consumidor financiero y las obligaciones de atencion, informacion y respuesta a quejas o reclamos.",
        "tema_juridico": "consumidor financiero",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["financiero", "reclamacion", "peticion"],
    },
    "ley_1480_2011": {
        "aliases": [
            "ley 1480 de 2011",
            "estatuto del consumidor",
            "consumidor ley 1480",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Congreso de la Republica",
        "numero_sentencia_o_norma": "Ley 1480 de 2011",
        "fecha": "2011-10-12",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/ley_1480_2011.html",
        "extracto_relevante": "Establece el Estatuto del Consumidor y refuerza el deber de informacion, la proteccion contra clausulas y practicas abusivas y el derecho a obtener reparacion.",
        "tema_juridico": "proteccion al consumidor",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["consumo", "reclamacion", "financiero"],
    },
    "ley_1581_2012": {
        "aliases": [
            "ley 1581 de 2012",
            "proteccion de datos personales",
            "tratamiento de datos personales",
            "supresion de datos",
        ],
        "tipo_fuente": "norma",
        "corporacion": "Congreso de la Republica",
        "numero_sentencia_o_norma": "Ley 1581 de 2012",
        "fecha": "2012-10-17",
        "url_verificada": "https://www.secretariasenado.gov.co/senado/basedoc/ley_1581_2012.html",
        "extracto_relevante": "Establece el regimen general de proteccion de datos personales, derechos del titular y reglas para el tratamiento de la informacion.",
        "tema_juridico": "proteccion de datos personales",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["habeas_data", "reclamacion", "peticion"],
    },
    "decreto_2555_2010": {
        "aliases": [
            "decreto 2555 de 2010",
            "decreto unico del sector financiero",
            "sector financiero decreto 2555",
        ],
        "tipo_fuente": "norma",
        "corporacion": "SUIN-Juriscol / Presidencia de la Republica",
        "numero_sentencia_o_norma": "Decreto 2555 de 2010",
        "fecha": "2010-07-15",
        "url_verificada": "https://www.suin-juriscol.gov.co/legislacion/decretosUnicos.html",
        "extracto_relevante": "Compila la reglamentacion del sector financiero y desarrolla deberes de informacion, transparencia y funcionamiento de entidades vigiladas.",
        "tema_juridico": "regulacion del sector financiero",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["financiero", "reclamacion"],
    },
    "circular_029_2014_sfc": {
        "aliases": [
            "circular externa 029 de 2014",
            "circular basica juridica",
            "proteccion al consumidor financiero sfc",
        ],
        "tipo_fuente": "guia_institucional",
        "corporacion": "Superintendencia Financiera de Colombia",
        "numero_sentencia_o_norma": "Circular Externa 029 de 2014",
        "fecha": "2014-06-26",
        "url_verificada": "https://www.superfinanciera.gov.co/publicaciones/11192/normativaproteccion-al-consumidor-financierocircular-basica-juridica-11192/",
        "extracto_relevante": "Reexpide la Circular Basica Juridica sobre proteccion al consumidor financiero y contiene instrucciones sobre acceso, informacion y practicas prohibidas en productos vigilados.",
        "tema_juridico": "proteccion al consumidor financiero",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["financiero", "reclamacion"],
    },
    "c_909_2012": {
        "aliases": [
            "c-909 de 2012",
            "sentencia c-909 de 2012",
            "c 909 de 2012",
        ],
        "tipo_fuente": "jurisprudencia",
        "corporacion": "Corte Constitucional",
        "numero_sentencia_o_norma": "Sentencia C-909 de 2012",
        "fecha": "2012-11-07",
        "url_verificada": "https://www.corteconstitucional.gov.co/relatoria/2012/c-909-12.htm",
        "extracto_relevante": "Reitera que en relaciones de consumo y financieras el ordenamiento puede limitar practicas o estipulaciones abusivas para proteger a la parte debil de la relacion contractual.",
        "tema_juridico": "clausulas y practicas abusivas",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["financiero", "reclamacion", "consumo"],
    },
    "t_517_2006": {
        "aliases": [
            "t-517 de 2006",
            "sentencia t-517 de 2006",
            "t 517 de 2006",
        ],
        "tipo_fuente": "jurisprudencia",
        "corporacion": "Corte Constitucional",
        "numero_sentencia_o_norma": "Sentencia T-517 de 2006",
        "fecha": "2006-07-07",
        "url_verificada": "https://www.corteconstitucional.gov.co/relatoria/2006/t-517-06.htm",
        "extracto_relevante": "Precisa que en actividades aseguradoras y financieras, por su interes publico, la autonomia contractual no ampara practicas abusivas ni dilaciones injustificadas en perjuicio del usuario.",
        "tema_juridico": "interes publico de la actividad aseguradora y limites a practicas abusivas",
        "nivel_confiabilidad": "alto",
        "source_level": 1,
        "uso": ["financiero", "reclamacion", "consumo"],
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


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL_VERIFIED_REGISTRY_PATH = ROOT / "knowledge_base" / "verified_legal_registry.json"


ACTION_SOURCE_KEYS: dict[str, list[str]] = {
    "accion de tutela": ["constitucion_art_86", "decreto_2591_art_14", "decreto_2591_art_42"],
    "accion de tutela por habeas data": ["constitucion_art_86", "decreto_2591_art_14", "decreto_2591_art_42", "constitucion_art_15", "ley_1266_2008", "ley_1581_2012"],
    "impugnacion de tutela": ["constitucion_art_86", "decreto_2591_art_14"],
    "incidente de desacato": ["constitucion_art_86", "decreto_2591_art_52"],
    "derecho de peticion": ["constitucion_art_23", "ley_1755_2015", "derecho_peticion_suin", "funcion_publica_peticion_1", "funcion_publica_peticion_2"],
    "derecho de peticion financiero": [
        "constitucion_art_23",
        "constitucion_art_78",
        "ley_1755_2015",
        "ley_1328_2009",
        "ley_1480_2011",
        "decreto_2555_2010",
        "circular_029_2014_sfc",
        "funcion_publica_peticion_1",
    ],
    "derecho de peticion a eps": ["constitucion_art_23", "ley_1755_2015", "constitucion_art_49", "ley_1751_2015", "funcion_publica_peticion_1"],
    "derecho de peticion laboral": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "derecho de peticion al proveedor": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "derecho de peticion a empresa de servicios": ["derecho_peticion_suin", "funcion_publica_peticion_1"],
    "reclamacion financiera": [
        "constitucion_art_13",
        "constitucion_art_15",
        "constitucion_art_23",
        "constitucion_art_78",
        "ley_1328_2009",
        "ley_1480_2011",
        "ley_1755_2015",
        "ley_1266_2008",
        "ley_1581_2012",
        "decreto_2555_2010",
        "circular_029_2014_sfc",
        "c_909_2012",
        "t_517_2006",
    ],
    "reclamo administrativo": ["constitucion_art_23", "ley_1755_2015"],
    "reclamo de consumo": ["derecho_peticion_suin"],
    "reclamacion por servicios publicos": ["constitucion_art_23", "ley_1755_2015"],
    "reclamacion de habeas data": ["constitucion_art_15", "ley_1266_2008", "ley_1581_2012", "constitucion_art_23", "ley_1755_2015"],
}


def _normalize_source_record(record: dict[str, Any]) -> dict[str, Any]:
    source_tier = _jurisprudence_source_tier(record)
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
        "source_tier": source_tier,
    }


def _append_verified_entry(
    *,
    entry: dict[str, Any],
    verified_sources: list[dict[str, Any]],
    verified_normas: list[str],
    verified_precedents: list[str],
) -> None:
    if entry.get("tipo_fuente") == "jurisprudencia":
        source_tier = _jurisprudence_source_tier(entry)
        if source_tier >= 99:
            return
    normalized = _normalize_source_record(entry)
    if normalized not in verified_sources:
        verified_sources.append(normalized)

    reference_name = entry["numero_sentencia_o_norma"]
    if entry.get("tipo_fuente") == "jurisprudencia":
        if reference_name not in verified_precedents:
            verified_precedents.append(reference_name)
        return

    if reference_name not in verified_normas:
        verified_normas.append(reference_name)


def _match_registry_entry(reference: str) -> dict[str, Any] | None:
    normalized = _lower(reference)
    compact = _compact_reference(reference)
    for entry in _get_verified_source_registry().values():
        aliases = [_lower(item) for item in entry.get("aliases", [])]
        compact_aliases = [_compact_reference(item) for item in entry.get("aliases", [])]
        compact_name = _compact_reference(entry.get("numero_sentencia_o_norma"))
        if any(alias and alias in normalized for alias in aliases):
            return entry
        if compact and any(alias and alias == compact for alias in compact_aliases):
            return entry
        if compact and compact_name == compact:
            return entry
        if compact and compact_name.startswith(compact):
            return entry
        if compact and any(alias and alias.startswith(compact) for alias in compact_aliases):
            return entry
    return None


def _load_external_verified_registry() -> dict[str, dict[str, Any]]:
    if not EXTERNAL_VERIFIED_REGISTRY_PATH.exists():
        return {}

    try:
        with open(EXTERNAL_VERIFIED_REGISTRY_PATH, "r", encoding="utf-8") as file:
            payload = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    records = payload.get("sources") if isinstance(payload, dict) else payload
    if not isinstance(records, dict):
        return {}

    normalized: dict[str, dict[str, Any]] = {}
    for key, record in records.items():
        if not isinstance(record, dict):
            continue
        if not record.get("numero_sentencia_o_norma"):
            continue
        aliases = record.get("aliases")
        if not isinstance(aliases, list) or not aliases:
            aliases = [record["numero_sentencia_o_norma"]]
        if record.get("tipo_fuente") == "jurisprudencia" and _jurisprudence_source_tier(record) >= 99:
            continue
        normalized[str(key)] = {
            **record,
            "aliases": [str(item).strip() for item in aliases if str(item).strip()],
            "source_level": int(record.get("source_level", 1)),
            "nivel_confiabilidad": str(record.get("nivel_confiabilidad") or "alto"),
        }
    return normalized


def _get_verified_source_registry() -> dict[str, dict[str, Any]]:
    external = _load_external_verified_registry()
    if not external:
        return VERIFIED_SOURCE_REGISTRY
    return {
        **VERIFIED_SOURCE_REGISTRY,
        **external,
    }


def _extract_legal_references(document: str) -> list[str]:
    text = str(document or "")
    patterns = [
        r"\b(?:T|SU|C)-\d{1,4}[A-Z]?(?:/\d{2,4})?\b",
        r"\bLey\s+\d{1,4}\s+de\s+\d{4}\b",
        r"\bDecreto\s+\d{1,4}\s+de\s+\d{4}\b",
        r"\b(?:Art(?:iculo|\.)?)\s+\d{1,3}\b",
        r"\bCircular(?:\s+Externa)?\s+\d{1,3}\s+de\s+\d{4}\b",
    ]
    found: list[str] = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    return list(dict.fromkeys(item.strip() for item in found if item.strip()))


def _article_reference_is_contextually_verified(
    reference: str,
    *,
    document: str,
    verified_names: set[str],
) -> bool:
    normalized = _lower(reference).strip()
    if not normalized.startswith("articulo"):
        return False
    article_number = re.findall(r"\d{1,3}", normalized)
    if not article_number:
        return False
    number = article_number[0]
    lowered_document = _lower(document)
    contextual_patterns = [
        rf"articulo\s+{number}\s+de\s+la\s+ley\s+\d{{1,4}}\s+de\s+\d{{4}}",
        rf"articulo\s+{number}\s+del\s+decreto\s+\d{{1,4}}\s+de\s+\d{{4}}",
        rf"articulo\s+{number}\s+de\s+decreto\s+\d{{1,4}}\s+de\s+\d{{4}}",
        rf"articulo\s+{number}\s+de\s+la\s+constitucion",
        rf"articulo\s+{number}\s+de\s+la\s+constitucion\s+politica",
    ]
    snippets: list[str] = []
    for pattern in contextual_patterns:
        snippets.extend(re.findall(pattern, lowered_document, flags=re.IGNORECASE))
    for snippet in snippets:
        if _match_registry_entry(snippet):
            return True
        if any(name and name in snippet for name in verified_names):
            return True
    return False


def validate_document_citations(
    *,
    document: str,
    source_validation_policy: dict[str, Any],
) -> dict[str, Any]:
    detected_references = _extract_legal_references(document)
    verified_registry = _get_verified_source_registry()
    verified_names = {
        _lower(item.get("numero_sentencia_o_norma"))
        for item in verified_registry.values()
        if item.get("numero_sentencia_o_norma")
    }
    verified_names.update(_lower(item) for item in (source_validation_policy.get("verified_normas") or []))
    verified_names.update(_lower(item) for item in (source_validation_policy.get("verified_precedents") or []))

    verified_detected: list[str] = []
    unresolved_detected: list[str] = []
    for reference in detected_references:
        normalized = _lower(reference)
        entry = _match_registry_entry(reference)
        if entry or normalized in verified_names or _article_reference_is_contextually_verified(reference, document=document, verified_names=verified_names):
            verified_detected.append(reference)
        else:
            unresolved_detected.append(reference)

    return {
        "detected_references": detected_references,
        "verified_detected_references": list(dict.fromkeys(verified_detected)),
        "unresolved_detected_references": list(dict.fromkeys(unresolved_detected)),
        "has_unverified_citations": bool(unresolved_detected),
    }


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

    category_key = _lower(category)
    if category_key == "salud":
        desired_keys.extend(["constitucion_art_49", "ley_1751_2015"])
    elif category_key == "bancos":
        desired_keys.extend(["ley_1328_2009", "ley_1266_2008"])
    elif category_key == "datos":
        desired_keys.extend(["constitucion_art_15", "ley_1266_2008", "ley_1581_2012"])

    desired_keys = list(dict.fromkeys(desired_keys))

    for key in desired_keys:
        entry = _get_verified_source_registry().get(key)
        if entry:
            _append_verified_entry(
                entry=entry,
                verified_sources=verified_sources,
                verified_normas=verified_normas,
                verified_precedents=verified_precedents,
            )

    for norma in legal_analysis.get("normas_relevantes") or []:
        entry = _match_registry_entry(str(norma))
        if entry:
            _append_verified_entry(
                entry=entry,
                verified_sources=verified_sources,
                verified_normas=verified_normas,
                verified_precedents=verified_precedents,
            )
        else:
            unresolved_normas.append(str(norma))

    for precedent in legal_analysis.get("precedentes_jurisprudenciales") or []:
        entry = _match_registry_entry(str(precedent))
        if entry and entry["tipo_fuente"] == "jurisprudencia":
            _append_verified_entry(
                entry=entry,
                verified_sources=verified_sources,
                verified_normas=verified_normas,
                verified_precedents=verified_precedents,
            )
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
