"""
Router Agent (Ultra-Light REST Version)
------------
Analyzes customer conversation using direct REST calls to Gemini API.
No heavy dependencies.
"""

import json
import os
from typing import List, Dict, Any
import httpx
from pydantic import BaseModel, Field

class RouterAgent:
    """Detects which business process applies to a customer conversation."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        
    def detect_process(self, messages: List[str]) -> Dict[str, Any]:
        conversation_text = "\n".join(messages)
        
        system_prompt = """Eres el Coordinador de Triaje de Aquaservice. Tu misión es analizar la conversación y determinar el proceso de negocio.

PROCESOS DISPONIBLES:
- STOP_REPARTO: El cliente quiere pausar, parar o anular su próximo reparto.
- SOCIAL: Saludos, despedidas, gracias o charla casual sin petición de negocio.
- UNKNOWN: No se identifica ninguno de los anteriores.

EXTRACCIÓN DE DATOS:
Si detectas STOP_REPARTO, intenta extraer:
- motivo: 'exceso_agua' (si tiene botellas de sobra) o 'ausencia_vacaciones' (si se va fuera).
- plan: 'Ahorro' o 'Planocho'.

FORMATO DE SALIDA (JSON ESTRICTO):
{
  "process": "NOMBRE_PROCESO",
  "confidence": 0.0-1.0,
  "extracted_data": {"campo": "valor"}
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
                
                # Extract text from Gemini response structure
                content_text = result['candidates'][0]['content']['parts'][0]['text']
                return json.loads(content_text)
        except Exception as e:
            print(f"Error in RouterAgent (REST): {e}")
            return {"process": "UNKNOWN", "confidence": 0, "extracted_data": {}}
