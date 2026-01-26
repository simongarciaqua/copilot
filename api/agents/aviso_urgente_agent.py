"""
Specialist Agent: Aviso Urgente (Full Quality REST Version)
-------------------------------------------------------
Generates high-quality business recommendations following the official manual.
"""

import json
import os
from typing import List, Dict, Any
from pathlib import Path
import httpx

class AvisoUrgenteAgent:
    """Specialist for the AVISO_URGENTE process at Aquaservice."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        self.policy_text = self._load_policy()
    
    def _load_policy(self) -> str:
        base_path = Path(__file__).parent.parent
        policy_path = base_path / "aviso_urgente" / "policy_aviso_urgente.txt"
        with open(policy_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_recommendation(
        self,
        messages: List[str],
        customer_context: Dict[str, Any],
        rules_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        conversation_text = "\n".join(messages)
        
        system_prompt = f"""Eres el Especialista en Aviso Urgente de Aquaservice. Tu misión es gestionar la creación de avisos urgentes o informar de su imposibilidad según la política.

POLÍTICA OFICIAL:
{self.policy_text}

REGLAS DE NEGOCIO (DECISIÓN TÉCNICA):
{json.dumps(rules_decision, indent=2, ensure_ascii=False)}

CONTEXTO DEL CLIENTE:
{json.dumps(customer_context, indent=2, ensure_ascii=False)}

INSTRUCCIONES CLAVE:
0. NO REPETIR PREGUNTAS: Si ya tenemos el producto o cantidad, pasa directo a validación.
1. FORMATO POR CANAL (CRÍTICO):
   - CANAL 'Telefono': Usa Bullet Points cortos y legibles con negritas. Evita párrafos largos.
   - CANAL 'Chat': Proporciona un guion conversacional completo en 'speech_sugerido'.
2. SI LA DECISIÓN ES 'RECHAZO_*':
   - NO puedes crear el aviso.
   - Debes informar al cliente el motivo usando EXACTAMENTE los 'ESCENARIOS DE RECHAZO' del manual.
   - Sé empático pero firme.

3. SI LA DECISIÓN ES 'AVISO_URGENTE_PERMITIDO':
   - Verifica si tenemos 'producto' y 'cantidad' en el CONTEXTO DEL CLIENTE o en la CONVERSACIÓN ACTUAL.
   - Si FALTAN datos: Pregunta por ellos (Paso 1 del Flujo).
   - Si TIENES datos: Verifica los MÍNIMOS (Paso 2).
     - Agua: min 1 botella.
     - Café: min 3 cajas.
   - Si cumple mínimos: CONFIRMA la creación e informa del plazo (Paso 3 y 4).

3. FORMATO SALIDA (JSON):
{{
  "titulo": "Resumen fase actual (ej: Validación, Solicitud Datos, Confirmación)",
  "objetivo": "Informar Rechazo | Pedir Datos | Confirmar Creación",
  "aviso_permitido": true | false,
  "speech_sugerido": "Guion para el agente",
  "siguiente_paso": "Acción técnica (ej: Crear Case Salesforce, Nada)",
  "gestion_finalizada": true | false
}}"""

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\nCONVERSACIÓN ACTUAL:\n{conversation_text}\n\nRespuesta JSON:"
                }]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.3
            }
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, json=payload)
                response.raise_for_status()
                result = response.json()
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(content_text)
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return data
        except Exception as e:
            print(f"Error in AvisoUrgenteAgent: {e}")
            return {"titulo": "Error", "speech_sugerido": "Error al conectar con la IA."}
