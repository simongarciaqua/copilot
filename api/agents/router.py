"""
Router Agent (Light Version)
------------
Analyzes customer conversation using official Google Generative AI SDK.
"""

import json
import os
from typing import List, Dict, Any
import google.generativeai as genai
from pydantic import BaseModel, Field

class ProcessDetection(BaseModel):
    """Schema for process detection output."""
    process: str = Field(description="The detected process name (e.g., STOP_REPARTO)")
    confidence: float = Field(description="Confidence score between 0 and 1")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Fields extracted from conversation")

class RouterAgent:
    """Detects which business process applies to a customer conversation."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model_name)
        
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

        prompt = f"{system_prompt}\n\nCONVERSACIÓN:\n{conversation_text}\n\nRespuesta JSON:"
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Error in RouterAgent: {e}")
            return {"process": "UNKNOWN", "confidence": 0, "extracted_data": {}}
