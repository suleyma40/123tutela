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
        self.client = OpenAI(api_key=api_key) if api_key and OpenAI else None

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
