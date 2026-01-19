"""
Router Agent
------------
Analyzes customer conversation and determines which process applies.
Uses LLM to detect intent and classify the request.
"""

from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
import os


class ProcessDetection(BaseModel):
    """Schema for process detection output."""
    process: str = Field(description="The detected process name (e.g., STOP_REPARTO)")
    confidence: float = Field(description="Confidence score between 0 and 1")
    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Fields extracted from conversation (e.g., motivo, plan)")


class RouterAgent:
    """Detects which business process applies to a customer conversation."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the router agent.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,  # Deterministic for classification
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.parser = JsonOutputParser(pydantic_object=ProcessDetection)
    
    def detect_process(self, messages: List[str]) -> Dict[str, Any]:
        """
        Analyze customer messages and detect which process applies.
        
        Args:
            messages: List of customer messages from the conversation
            
        Returns:
            Dictionary with:
            - process: Process name (e.g., "STOP_REPARTO")
            - confidence: Confidence score (0-1)
        """
        # Build conversation context
        conversation_text = "\n".join([f"Cliente: {msg}" for msg in messages])
        
        # System prompt for process detection
        system_prompt = """Eres un experto en clasificación y extracción de entidades para atención al cliente. Tu misión es detectar el proceso y extraer variables clave de la conversación.

PROCESOS DISPONIBLES:
- STOP_REPARTO: Solicitudes para pausar, detener o modificar entregas (vacaciones, exceso de stock, cambios de frecuencia).
- SOCIAL: Saludos, despedidas, agradecimientos o charla trivial que no requiere una gestión de negocio (ej: "hola", "¿cómo estás?", "gracias", "buenos días").

REGLAS DE EXTRACCIÓN SEMÁNTICA:
Para el campo 'motivo', mapea la intención del cliente a uno de estos códigos: (Solo si el proceso es STOP_REPARTO)

1. 'exceso_agua': El cliente tiene demasiado producto.
   Ejemplos: "me sobran botellas", "tengo stock acumulado", "el salón parece un almacén", "no he abierto las del último mes", "voy sobrado de litros", "no me traigas más agua que no la gasto".

2. 'ausencia_vacaciones': El cliente no estará físicamente en el domicilio.
   Ejemplos: "me voy fuera", "no estaré en casa", "cierro por descanso", "el piso estará vacío", "estoy de viaje", "me voy a mi segunda residencia", "no voy a estar para recibir el pedido".

3. 'otro': Motivos no contemplados anteriormente.

FORMATO DE SALIDA:
Debes responder ÚNICAMENTE con un JSON que siga este esquema:
{
    "process": "STOP_REPARTO", "SOCIAL" o "UNKNOWN",
    "confidence": 0.0 a 1.0,
    "extracted_data": {
        "motivo": "exceso_agua", "ausencia_vacaciones" o "otro",
        "plan": "Ahorro" o "Planocho" (si se menciona)
    }
}

REGLA DE ORO: Analiza el SENTIDO de la frase, no solo las palabras individuales. Un cliente que dice "ya no me cabe más agua en casa" tiene el motivo 'exceso_agua'."""

        human_prompt = f"""Analiza esta conversación y detecta el proceso:

{conversation_text}

Responde en JSON:"""

        # Call LLM
        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ])
        
        # Parse JSON response
        try:
            result = self.parser.parse(response.content)
            return result
        except Exception as e:
            # Fallback if parsing fails
            return {
                "process": "UNKNOWN",
                "confidence": 0.0,
                "error": str(e)
            }


def create_router_agent(model_name: str = None) -> RouterAgent:
    """
    Factory function to create a router agent.
    
    Args:
        model_name: Optional model name override
        
    Returns:
        RouterAgent instance
    """
    if model_name is None:
        model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash-exp")
    
    return RouterAgent(model_name=model_name)
