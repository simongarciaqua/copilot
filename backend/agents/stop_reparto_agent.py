"""
Specialist Agent: Stop Reparto (Light Version)
--------------------------------------------
Generates business recommendations using official Google Generative AI SDK.
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path
import google.generativeai as genai
from pydantic import BaseModel, Field

class AgentRecommendation(BaseModel):
    """Schema for agent recommendation output."""
    titulo: str
    objetivo: str
    stop_permitido: bool
    speech_sugerido: str
    siguiente_paso: str
    gestion_finalizada: bool = False

class StopRepartoAgent:
    """Specialist for the STOP_REPARTO process at Aquaservice."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name)
        self.policy_text = self._load_policy()
    
    def _load_policy(self) -> str:
        base_path = Path(__file__).parent.parent
        policy_path = base_path / "stop_reparto" / "policy_stop_reparto.txt"
        with open(policy_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_recommendation(
        self,
        messages: List[str],
        customer_context: Dict[str, Any],
        rules_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        conversation_text = "\n".join(messages)
        
        system_prompt = f"""Eres el Especialista en Stop Reparto de Aquaservice. Tu objetivo es guiar al agente para que siga el MANUAL DE POLÍTICA.

MANUAL DE POLÍTICA:
{self.policy_text}

REGLAS DETERMINISTAS (VINCULANTES):
{json.dumps(rules_decision, indent=2, ensure_ascii=False)}

REGLAS DE COMPORTAMIENTO:
1. BREVEDAD: El agente está al teléfono. Usa frases cortas y Bullet Points.
2. VINCULACIÓN: Solo puedes ofrecer acciones en `allowed_actions`. Prohibido ofrecer stop_0euros si no está ahí.
3. LÍMITES: Si `stops_ultimo_ano` >= 2, no ofrezcas Stops.
4. FCR: Si el cliente acepta, marca `gestion_finalizada: true`.

FORMATO DE SALIDA (JSON):
{{
  "titulo": "Título corto",
  "objetivo": "Reconducción/FCR/Retención",
  "stop_permitido": true/false,
  "speech_sugerido": "Texto para el agente",
  "siguiente_paso": "Ruta Salesforce",
  "gestion_finalizada": true/false
}}"""

        prompt = f"{system_prompt}\n\nCONVERSACIÓN:\n{conversation_text}\n\nCONTEXTO:\n{json.dumps(customer_context)}\n\nRespuesta JSON:"
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error in StopRepartoAgent: {e}")
            return {
                "titulo": "Error en Recomendación",
                "objetivo": "Soporte",
                "stop_permitido": False,
                "speech_sugerido": "Lo siento, ha habido un error al generar la recomendación personalizada.",
                "siguiente_paso": "Continuar de forma manual según política.",
                "gestion_finalizada": False
            }
