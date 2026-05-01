from __future__ import annotations

import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from backend.legal_prompts import LEGAL_SALUD_DIAGNOSIS_SYSTEM_PROMPT, LEGAL_SALUD_STRATEGY_SYSTEM_PROMPT

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
        action = "Accion de tutela"

        if "salud" in problem or "eps" in problem:
            rights.extend(["Derecho fundamental a la salud", "Vida digna"])
            rules.extend(
                [
                    "Constitucion Politica de 1991, articulo 49",
                    "Ley Estatutaria 1751 de 2015",
                    "Constitucion Politica de 1991, articulo 86",
                ]
            )
        if "datos" in problem or "habeas" in problem:
            rights.extend(["Habeas data", "Buen nombre"])
            rules.extend(
                [
                    "Constitucion Politica de 1991, articulo 15",
                    "Ley 1266 de 2008",
                    "Ley 1581 de 2012",
                ]
            )
            action = "Reclamacion de habeas data"
        if "laboral" in problem or "despido" in problem:
            rights.extend(["Minimo vital", "Trabajo digno"])
            rules.append("Constitucion Politica de 1991, articulo 25")
        if "banco" in problem or "tarjeta" in problem or "cobro" in problem or "financier" in problem:
            rights.extend(["Proteccion del consumidor financiero", "Debido proceso contractual"])
            rules.extend(["Ley 1328 de 2009", "Constitucion Politica de 1991, articulo 23"])
            action = "Reclamacion financiera"

        if not rights:
            for article in kb.get("constitucion_politica_1991", {}).get("articulos", []):
                rights.append(article["derecho"])
                rules.append(f"Constitucion Politica Art. {article['id']}")
                break

        return {
            "derechos_vulnerados": list(dict.fromkeys(rights)),
            "normas_relevantes": list(dict.fromkeys(rules)),
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

    def _financial_case_summary(self, intake_form: dict[str, Any], facts: dict[str, Any], description: str) -> str:
        entity = str(intake_form.get("target_entity") or "la entidad financiera").strip()
        product = str(intake_form.get("bank_product_type") or "un producto financiero").strip()
        charge = str(intake_form.get("disputed_charge") or "un cobro no autorizado").strip()
        amount = str(intake_form.get("bank_amount_involved") or "").strip()
        event_date = str(intake_form.get("bank_event_date") or intake_form.get("key_dates") or "").strip()
        story = str(intake_form.get("case_story") or facts.get("hechos_principales") or description or "").lower()

        if "seguro" in story or "seguro" in charge.lower():
            summary = (
                f"La persona usuaria manifiesta que {entity} viene facturando en {product} "
                f"cobros asociados a {charge}, sin que exista autorizacion previa, expresa e informada de su parte"
            )
        else:
            summary = (
                f"La persona usuaria reporta inconsistencias frente a {product} administrado por {entity}, "
                f"particularmente respecto de {charge}"
            )

        details: list[str] = []
        if event_date:
            details.append(f"hechos advertidos desde {event_date}")
        if amount:
            details.append(f"por un valor aproximado de {amount}")
        if details:
            summary += ", " + ", ".join(details)
        return self._formalize_text(summary)

    def _health_case_summary(self, intake_form: dict[str, Any], facts: dict[str, Any], description: str) -> str:
        entity = str(intake_form.get("target_entity") or intake_form.get("eps_name") or "la EPS o entidad de salud").strip()
        diagnosis = str(intake_form.get("diagnosis") or "una condicion medica que requiere atencion continua").strip()
        treatment = str(intake_form.get("treatment_needed") or "el servicio de salud requerido").strip()
        event_date = str(intake_form.get("event_date") or intake_form.get("key_dates") or "").strip()
        urgency = str(intake_form.get("urgency_detail") or intake_form.get("current_harm") or "").strip()

        summary = (
            f"La persona usuaria informa que {entity} ha incurrido en barreras de acceso, demora o negativa injustificada "
            f"frente a {treatment}, pese a que dicho manejo resulta necesario en el contexto de {diagnosis}"
        )
        details: list[str] = []
        if event_date:
            details.append(f"situacion advertida desde {event_date}")
        if urgency:
            details.append(f"con afectacion actual consistente en {urgency}")
        if details:
            summary += ", " + ", ".join(details)
        return self._formalize_text(summary)

    def _data_case_summary(self, intake_form: dict[str, Any], facts: dict[str, Any], description: str) -> str:
        entity = str(intake_form.get("target_entity") or "la entidad que trata los datos").strip()
        disputed_data = str(intake_form.get("disputed_data") or "un dato o reporte personal cuestionado").strip()
        requested_action = str(intake_form.get("requested_data_action") or "corregir o suprimir la informacion").strip()
        event_date = str(intake_form.get("event_date") or intake_form.get("key_dates") or "").strip()

        summary = (
            f"La persona usuaria reporta que {entity} mantiene o divulga {disputed_data}, "
            f"y solicita {requested_action} por considerar que el tratamiento actual resulta improcedente, inexacto o desactualizado"
        )
        if event_date:
            summary += f", con conocimiento del hecho desde {event_date}"
        return self._formalize_text(summary)

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
        category_key = str(category or "").lower()
        if category_key == "bancos":
            case_story = self._financial_case_summary(intake_form, facts, description)
        elif category_key == "salud":
            case_story = self._health_case_summary(intake_form, facts, description)
        elif category_key == "datos":
            case_story = self._data_case_summary(intake_form, facts, description)
        else:
            case_story = self._formalize_text(intake_form.get("case_story") or facts.get("hechos_principales") or description)
        if case_story:
            chronology.append(case_story)
        key_dates = self._formalize_text(intake_form.get("key_dates") or facts.get("fechas_mencionadas"))
        if key_dates:
            chronology.append(f"Los hitos temporales informados para este caso se resumen asi: {key_dates}")

        prior_claim = str(intake_form.get("prior_claim") or "").strip()
        prior_claim_date = self._formalize_text(intake_form.get("prior_claim_date"))
        prior_claim_result = self._formalize_text(intake_form.get("prior_claim_result"))
        if prior_claim == "si" and prior_claim_date:
            chronology.append(f"Con anterioridad, la persona usuaria presento reclamacion directa ante la entidad en fecha {prior_claim_date}")
        if prior_claim == "si" and prior_claim_result:
            chronology.append(f"Frente a dicha gestion previa, la entidad emitio la siguiente respuesta o actuacion: {prior_claim_result}")
        elif prior_claim == "no":
            chronology.append("A la fecha no se evidencia una solucion efectiva de fondo por parte de la entidad involucrada.")

        regeneration_reason = self._formalize_text(intake_form.get("regeneration_reason"))
        regeneration_context = self._formalize_text(intake_form.get("regeneration_additional_context"))

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
        if regeneration_reason or regeneration_context:
            failures.append("El caso requiere una respuesta de fondo que incluya la devolucion integral de los valores discutidos y una explicacion documentada sobre el origen del cobro.")

        pretensions: list[str] = []
        concrete_request = self._formalize_text(intake_form.get("concrete_request") or facts.get("pretension_concreta"))
        if concrete_request:
            pretensions.append(concrete_request)
        if regeneration_reason or regeneration_context:
            pretensions.append("Que la entidad reintegre los valores cobrados por conceptos no autorizados, junto con los ajustes a que haya lugar, y remita soporte verificable de la correccion aplicada.")
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

    def _ask_json_with_system(self, *, prompt: str, system_prompt: str | None) -> dict[str, Any]:
        if not self.client:
            raise RuntimeError("OpenAI no está configurado en este entorno.")
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
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
            problem_text = json.dumps(fact_data, ensure_ascii=False).lower()
            is_health_case = any(token in problem_text for token in ("salud", "eps", "ips", "medic", "tratamiento", "cita"))
            return self._ask_json_with_system(
                prompt=prompt,
                system_prompt=LEGAL_SALUD_DIAGNOSIS_SYSTEM_PROMPT if is_health_case else None,
            )
        except Exception:
            return self._fact_fallback(user_description, category)

    def layer_2_legal_matching(self, fact_data: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            return self._legal_match_fallback(fact_data)

        kb_summary = json.dumps(self.knowledge_base, ensure_ascii=False)
        prompt = f"""
        Actúa como un abogado experto en derecho constitucional colombiano.
        Usando esta base jurídica colombiana:
        {kb_summary}

        Y estos hechos reportados por el usuario:
        {json.dumps(fact_data, ensure_ascii=False)}

        Tu tarea principal es DIAGNOSTICAR la acción legal correcta.
        REGLAS DE DIAGNÓSTICO:
        - Si hay riesgo vital inmediato, menor enfermo, perjuicio irremediable, o si el usuario ya presentó una queja/petición y no le resolvieron la barrera -> "Accion de tutela" (workflow_type: "tutela").
        - Si es el primer contacto sin urgencia vital y no se ha reclamado formalmente antes -> "Derecho de peticion a EPS" (workflow_type: "derecho_peticion").
        - Si ya hubo un fallo de tutela favorable pero fue incumplido -> "Incidente de desacato" (workflow_type: "desacato").
        - Si hay un fallo de tutela desfavorable reciente y hay argumentos -> "Impugnacion de tutela" (workflow_type: "impugnacion").

        Responde solo JSON con:
        - derechos_vulnerados (lista de strings)
        - normas_relevantes (lista de strings)
        - precedentes_jurisprudenciales (lista de strings)
        - recommended_action (string exacto según las reglas)
        - workflow_type (string exacto según las reglas)
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
                messages=[
                    {"role": "system", "content": LEGAL_SALUD_STRATEGY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
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
