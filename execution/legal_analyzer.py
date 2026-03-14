import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class LegalAnalyzer:
    def __init__(self, knowledge_base_path):
        with open(knowledge_base_path, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)

    def layer_1_fact_extraction(self, user_description):
        """Extract facts and key elements from user description."""
        prompt = f"""
        Como un experto abogado colombiano, analiza la descripción del caso del usuario y extrae:
        - Hechos principales (resumidos)
        - Entidades involucradas (EPS, banco, empleador, etc.)
        - Fechas mencionadas
        - Problema central (negación de servicio, despido, mora, etc.)

        Descripción del caso:
        {user_description}

        Responde únicamente en formato JSON.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(response.choices[0].message.content)

    def layer_2_legal_matching(self, fact_data):
        """Match extracted facts with the Colombian legal framework (Knowledge Base)."""
        kb_summary = json.dumps(self.knowledge_base, indent=2, ensure_ascii=False)
        
        prompt = f"""
        Usando la siguiente Base de Conocimiento Jurídico Colombiano:
        {kb_summary}

        Y los siguientes hechos del caso extraídos:
        {json.dumps(fact_data, indent=2, ensure_ascii=False)}

        Identifica:
        1. Derechos vulnerados (según la Constitución y leyes específicas).
        2. Normas relevantes aplicables.
        3. Precedentes jurisprudenciales si aplican.

        Responde únicamente en formato JSON.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0
        )
        return json.loads(response.choices[0].message.content)

    def layer_3_strategy_recommendation(self, legal_match_data):
        """Recommend the best legal strategy and suggest action."""
        prompt = f"""
        Basado en el análisis jurídico realizado:
        {json.dumps(legal_match_data, indent=2, ensure_ascii=False)}

        Dime cuál es la mejor estrategia legal a seguir.
        - Acción recomendada (Tutela, Derecho de Petición, Incidente de Desacato, Acción Popular, Reclamación Adm, etc.)
        - Justificación de por qué es la mejor opción.
        - Lo que la app generará automáticamente (Petición central y fundamentos jurídicos).

        Responde en lenguaje natural empático y profesional, adecuado para el usuario en la app.
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content

    def full_analysis(self, user_description):
        """Run all 3 layers and return the final analysis."""
        try:
            facts = self.layer_1_fact_extraction(user_description)
            legal_analysis = self.layer_2_legal_matching(facts)
            final_strategy = self.layer_3_strategy_recommendation(legal_analysis)
            
            return {
                "success": True,
                "facts": facts,
                "legal_analysis": legal_analysis,
                "strategy": final_strategy
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    analyzer = LegalAnalyzer('knowledge_base/marcos_normativos.json')
    # Example for testing
    test_case = "Llevo 3 meses pidiendo una cita con el cardiólogo a mi EPS Sura y no me dan fecha. Ya instauré un reclamo verbal y no pasa nada."
    result = analyzer.full_analysis(test_case)
    print(json.dumps(result, indent=2, ensure_ascii=False))
