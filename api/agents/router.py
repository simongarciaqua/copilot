"""
Router Agent (Full Quality REST Version)
------------
Analyzes customer conversation using direct REST calls to Gemini API.
Includes full context and few-shot examples for high accuracy.
"""

import json
import os
from typing import List, Dict, Any
import httpx

class RouterAgent:
    """Detects which business process applies to a customer conversation."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        
    def detect_process(self, messages: List[str]) -> Dict[str, Any]:
        conversation_text = "\n".join(messages)
        
        system_prompt = """Eres el Coordinador de Triaje de Aquaservice. Tu misión es analizar la conversación y determinar el proceso de negocio y extraer datos clave.

PROCESOS DISPONIBLES:
- STOP_REPARTO: El cliente quiere pausar, parar, anular o mover su reparto programado.
- AVISO_URGENTE: El cliente necesita producto urgentemente, se ha quedado sin agua o café, o pide un reparto extra fuera de su fecha habitual.
- SOCIAL: Saludos, despedidas, gracias o charla casual.
- UNKNOWN: No se identifica ninguno de los anteriores.

REGLAS DE DISTINCIÓN:
- Si el cliente dice "tengo mucha agua", "no vengas", "anula el pedido" -> STOP_REPARTO.
- Si el cliente dice "pásate ya", "necesito botellas", "me he quedado sin nada" -> AVISO_URGENTE.

EXTRACCIÓN DE ENTIDADES (Importante):
1. Para STOP_REPARTO:
   - 'motivo': 'exceso_agua' (si tiene agua), 'ausencia_vacaciones' (si no está)
   - 'plan': 'Ahorro' (4 sem), 'Planocho' (8 sem)
   - 'es_puntual': true (si dice "esta vez", "solo hoy", "puntual") o false
2. Para AVISO_URGENTE:
   - 'producto': 'agua', 'cafe'
   - 'cantidad': número o descripción (ej: "2 botellas")

EJEMPLOS:
- "Hola, quiero un stop reparto de manera puntual" -> process: STOP_REPARTO, es_puntual: true
- "Hola, necesito agua urgente" -> process: AVISO_URGENTE, producto: agua
- "Oye, que me voy de vacaciones y quiero parar el pedido" -> process: STOP_REPARTO, motivo: ausencia_vacaciones
- "Me he quedado sin cápsulas, ¿podéis traerme?" -> process: AVISO_URGENTE, producto: cafe
- "Buenas tardes, ¿cómo va todo?" -> process: SOCIAL

FORMATO DE SALIDA (JSON ESTRICTO):
{
  "process": "STOP_REPARTO" | "AVISO_URGENTE" | "SOCIAL" | "UNKNOWN",
  "confidence": 0.0-1.0,
  "extracted_data": {
     "motivo": string | null,
     "plan": string | null,
     "es_puntual": boolean | null,
     "producto": string | null,
     "cantidad": string | number | null
  }
}"""

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"{system_prompt}\n\nCONVERSACIÓN:\n{conversation_text}\n\nRespuesta JSON:"
                }]
            }],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1
            }
        }
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(self.api_url, json=payload)
                response.raise_for_status()
                result = response.json()
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                data = json.loads(content_text)
                # Handle case where Gemini returns a list instead of a dict
                if isinstance(data, list) and len(data) > 0:
                    return data[0]
                return data
        except Exception as e:
            print(f"Error in RouterAgent: {e}")
            return {"process": "UNKNOWN", "confidence": 0, "extracted_data": {}}
