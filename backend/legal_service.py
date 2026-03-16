from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv

load_dotenv()

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


class LegalAnalyzer:
    def __init__(self, knowledge_base_path: str):
        with open(knowledge_base_path, "r", encoding="utf-8") as file:
            self.knowledge_base = json.load(file)

        api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "18"))
        max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "1"))
        self.client = (
            OpenAI(api_key=api_key, timeout=timeout_seconds, max_retries=max_retries)
            if api_key and OpenAI
            else None
        )

    def _extract_entities(self, user_description: str) -> list[str]:
        patterns = [
            r"\bEPS\s+[A-ZÁÉÍÓÚ][\wÁÉÍÓÚáéíóú-]*",
            r"\bBancolombia\b",
            r"\bDavivienda\b",
            r"\bSura\b",
            r"\bNueva EPS\b",
            r"\bSanitas\b",
            r"\bCompensar\b",
        ]
        found = []
        for pattern in patterns:
            found.extend(re.findall(pattern, user_description, flags=re.IGNORECASE))
        return sorted({item.strip() for item in found if item.strip()})

    def _fact_fallback(self, user_description: str, category: str | None = None) -> dict[str, Any]:
        sentences = [part.strip() for part in re.split(r"[.!?]\s+", user_description) if part.strip()]
        dates = re.findall(
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d+\s+(?:mes|meses|día|días|semana|semanas)\b",
            user_description,
            flags=re.IGNORECASE,
        )
        problem = "Vulneración de derechos"
        lowered = user_description.lower()

        if any(word in lowered for word in ["eps", "médico", "medico", "cita", "tratamiento", "salud"]):
            problem = "Barreras de acceso a salud"
        elif any(word in lowered for word in ["despido", "salario", "liquidación", "laboral"]):
            problem = "Conflicto laboral"
        elif any(word in lowered for word in ["banco", "cobro", "datacrédito", "datacredito"]):
            problem = "Conflicto financiero"

        return {
            "hechos_principales": " ".join(sentences[:3]) or user_description.strip(),
            "entidades_involucradas": self._extract_entities(user_description),
            "fechas_mencionadas": dates,
            "problema_central": category or problem,
        }

    def _legal_match_fallback(self, fact_data: dict[str, Any]) -> dict[str, Any]:
        kb = self.knowledge_base
        problem = json.dumps(fact_data, ensure_ascii=False).lower()
        rights = []
        rules = []
        precedents = []
        action = "Acción de tutela"

        if "salud" in problem or "eps" in problem:
            rights.append("Derecho fundamental a la salud")
            rules.extend(["Constitución Política Art. 49", "Ley 1751 de 2015"])
            precedents.append("T-760 de 2008")
        if "datos" in problem or "habeas" in problem:
            rights.append("Habeas Data")
            rules.append("Constitución Política Art. 15")
            action = "Derecho de petición"
        if "laboral" in problem or "despido" in problem:
            rights.extend(["Mínimo vital", "Trabajo digno"])
            rules.append("Constitución Política Art. 25")

        if not rights:
            for article in kb.get("constitucion_politica_1991", {}).get("articulos", []):
                rights.append(article["derecho"])
                rules.append(f"Constitución Política Art. {article['id']}")
                break

        if not precedents and kb.get("jurisprudencia_hito"):
            precedents = list(kb["jurisprudencia_hito"].keys())[:1]

        return {
            "derechos_vulnerados": rights,
            "normas_relevantes": rules,
            "precedentes_jurisprudenciales": precedents,
            "recommended_action": action,
        }

    def _strategy_fallback(self, legal_match_data: dict[str, Any]) -> str:
        rights = legal_match_data.get("derechos_vulnerados") or []
        rules = legal_match_data.get("normas_relevantes") or []
        action = legal_match_data.get("recommended_action") or "Acción jurídica"
        rights_text = ", ".join(rights) if isinstance(rights, list) else str(rights)
        rules_text = ", ".join(rules) if isinstance(rules, list) else str(rules)
        return (
            f"Con la información disponible, la ruta más sólida es presentar una {action}. "
            f"La app identificó posibles afectaciones a {rights_text}. "
            f"Como soporte principal usaremos {rules_text}. "
            "Ahora podemos generar un borrador con hechos, fundamentos y destinatario sugerido."
        )

    def _formalize_text(self, value: str | None) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        text = re.sub(r"\s+", " ", text)
        text = text[:1].upper() + text[1:]
        if text[-1] not in ".;:":
            text += "."
        return text

    def _document_insights_fallback(
        self,
        *,
        description: str,
        category: str | None,
        facts: dict[str, Any],
        legal_analysis: dict[str, Any],
        intake_form: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        intake_form = intake_form or {}
        chronology: list[str] = []
        case_story = self._formalize_text(intake_form.get("case_story") or facts.get("hechos_principales") or description)
        if case_story:
            chronology.append(case_story)
        key_dates = self._formalize_text(intake_form.get("key_dates") or facts.get("fechas_mencionadas"))
        if key_dates:
            chronology.append(f"Las referencias temporales relevantes del caso son las siguientes: {key_dates}")

        prior_claim = str(intake_form.get("prior_claim") or "").strip()
        prior_claim_result = self._formalize_text(intake_form.get("prior_claim_result"))
        if prior_claim == "si" and prior_claim_result:
            chronology.append(f"Con anterioridad, la persona usuaria promovio reclamacion directa y recibio la siguiente respuesta: {prior_claim_result}")
        elif prior_claim == "no":
            chronology.append("A la fecha no se evidencia una solucion efectiva de fondo por parte de la entidad involucrada.")

        regeneration_reason = self._formalize_text(intake_form.get("regeneration_reason"))
        regeneration_context = self._formalize_text(intake_form.get("regeneration_additional_context"))
        if regeneration_reason:
            chronology.append(f"En esta nueva revision, la persona usuaria precisa que el documento anterior requiere mejora por la siguiente razon: {regeneration_reason}")
        if regeneration_context:
            chronology.append(f"Como informacion adicional relevante para la presente redaccion se incorpora lo siguiente: {regeneration_context}")

        failures: list[str] = []
        lowered = f"{description} {case_story}".lower()
        if any(token in lowered for token in ["no autorice", "no autoricé", "sin autorizacion", "sin autorización"]):
            failures.append("La entidad registra o cobra conceptos sin que exista autorizacion clara, previa e informada del titular.")
        if any(token in lowered for token in ["cobro", "cuota", "seguro", "cargo", "debito"]):
            failures.append("La entidad no explica de forma suficiente el origen, soporte contractual y trazabilidad de los cobros cuestionados.")
        if any(token in lowered for token in ["no responde", "sin respuesta", "no contest", "no resuelve"]):
            failures.append("La entidad omite suministrar una respuesta completa, verificable y oportuna frente a la situacion reclamada.")
        if not failures:
            failures.append("Se advierte una actuacion presuntamente irregular de la entidad que exige verificacion, correccion y respuesta de fondo.")

        pretensions: list[str] = []
        concrete_request = self._formalize_text(intake_form.get("concrete_request") or facts.get("pretension_concreta"))
        if concrete_request:
            pretensions.append(concrete_request)
        pretensions.append("Que la entidad emita respuesta integral, motivada y verificable frente a cada uno de los puntos reclamados.")

        rights = legal_analysis.get("derechos_vulnerados") or []
        rules = legal_analysis.get("normas_relevantes") or []
        legal_basis_summary = (
            f"El caso compromete principalmente {', '.join(rights) if rights else 'garantias del usuario'} y puede sustentarse, entre otras, en las siguientes bases: {', '.join(rules) if rules else 'normativa general aplicable'}."
        )
        return {
            "chronology": chronology,
            "entity_failures": failures,
            "pretensions": pretensions,
            "legal_basis_summary": legal_basis_summary,
            "narrative_summary": self._formalize_text(facts.get("problema_central") or category or description),
        }

    def _ask_json(self, prompt: str) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI no está configurado en este entorno.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return json.loads(response.choices[0].message.content or "{}")

    def layer_1_fact_extraction(self, user_description: str, category: str | None = None) -> dict[str, Any]:
        if not self.client:
            return self._fact_fallback(user_description, category)

        prompt = f"""
        Analiza este caso legal en Colombia y responde solo JSON con estas llaves:
        hechos_principales, entidades_involucradas, fechas_mencionadas, problema_central.

        Categoría declarada por el usuario: {category or 'No indicada'}
        Descripción:
        {user_description}
        """
        try:
            return self._ask_json(prompt)
        except Exception:
            return self._fact_fallback(user_description, category)

    def layer_2_legal_matching(self, fact_data: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            return self._legal_match_fallback(fact_data)

        kb_summary = json.dumps(self.knowledge_base, ensure_ascii=False)
        prompt = f"""
        Usando esta base jurídica colombiana:
        {kb_summary}

        Y estos hechos:
        {json.dumps(fact_data, ensure_ascii=False)}

        Responde solo JSON con:
        derechos_vulnerados, normas_relevantes, precedentes_jurisprudenciales, recommended_action.
        """
        try:
            return self._ask_json(prompt)
        except Exception:
            return self._legal_match_fallback(fact_data)

    def layer_3_strategy_recommendation(self, legal_match_data: dict[str, Any]) -> str:
        if not self.client:
            return self._strategy_fallback(legal_match_data)

        prompt = f"""
        Con base en este análisis legal:
        {json.dumps(legal_match_data, ensure_ascii=False)}

        Escribe una recomendación breve, empática y accionable para un usuario no abogado.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return response.choices[0].message.content or self._strategy_fallback(legal_match_data)
        except Exception:
            return self._strategy_fallback(legal_match_data)

    def full_analysis(self, user_description: str, category: str | None = None) -> dict[str, Any]:
        try:
            facts = self.layer_1_fact_extraction(user_description, category=category)
            legal_analysis = self.layer_2_legal_matching(facts)
            final_strategy = self.layer_3_strategy_recommendation(legal_analysis)
            return {
                "success": True,
                "facts": facts,
                "legal_analysis": legal_analysis,
                "strategy": final_strategy,
            }
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    def compose_document_insights(
        self,
        *,
        description: str,
        category: str | None,
        facts: dict[str, Any],
        legal_analysis: dict[str, Any],
        intake_form: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        fallback = self._document_insights_fallback(
            description=description,
            category=category,
            facts=facts,
            legal_analysis=legal_analysis,
            intake_form=intake_form,
        )
        intake_form = intake_form or {}
        if intake_form.get("regeneration_reason") or intake_form.get("regeneration_additional_context"):
            return fallback
        if not self.client:
            return fallback

        prompt = f"""
        Actua como abogado litigante en Colombia. Convierte la narracion del cliente en insumos juridicos formales para un documento presentable.
        Responde solo JSON con estas llaves:
        chronology, entity_failures, pretensions, legal_basis_summary, narrative_summary.

        Reglas:
        - chronology: lista de 3 a 6 hechos en orden cronologico, redactados de manera formal y objetiva.
        - entity_failures: lista de 2 a 5 fallas concretas atribuibles a la entidad.
        - pretensions: lista de 2 a 5 pretensiones juridicas claras, medibles y ejecutables.
        - legal_basis_summary: un parrafo breve y formal con sustento juridico.
        - narrative_summary: un parrafo corto que sintetice el conflicto sin repetir literalmente al cliente.

        Categoria: {category or 'No indicada'}
        Descripcion original del cliente:
        {description}

        Hechos estructurados:
        {json.dumps(facts, ensure_ascii=False)}

        Analisis legal:
        {json.dumps(legal_analysis, ensure_ascii=False)}

        Intake:
        {json.dumps(intake_form or {}, ensure_ascii=False)}

        Si existe retroalimentacion de regeneracion, debes usarla para corregir redaccion, justificar mejor el caso o incorporar datos faltantes.
        """
        try:
            result = self._ask_json(prompt)
            return {
                "chronology": result.get("chronology") or fallback["chronology"],
                "entity_failures": result.get("entity_failures") or fallback["entity_failures"],
                "pretensions": result.get("pretensions") or fallback["pretensions"],
                "legal_basis_summary": result.get("legal_basis_summary") or fallback["legal_basis_summary"],
                "narrative_summary": result.get("narrative_summary") or fallback["narrative_summary"],
            }
        except Exception:
            return fallback
