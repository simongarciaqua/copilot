"""
STOP_REPARTO Specialist Agent
------------------------------
Generates recommendations for customer service agents handling stop delivery requests.
Strictly follows rules engine decisions and policy guidelines.
"""

from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from pathlib import Path
import os
import json


class AgentRecommendation(BaseModel):
    """Schema for agent recommendation output."""
    titulo: str = Field(description="Título principal de la acción recomendada")
    objetivo: str = Field(description="Objetivo de la interacción (Reconducción, Retención, FCR)")
    stop_permitido: bool = Field(description="Si se permite stop según reglas")
    speech_sugerido: str = Field(description="Speech sugerido para el agente, copiable")
    siguiente_paso: str = Field(description="Qué hacer si el cliente rechaza")
    gestion_finalizada: bool = Field(default=False, description="True si el cliente ha aceptado o el proceso ha concluido (FCR)")


class StopRepartoAgent:
    """Specialist agent for STOP_REPARTO process."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        """
        Initialize the specialist agent.
        
        Args:
            model_name: Name of the LLM model to use
        """
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.7,  # Higher for more natural variation in speech
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.parser = JsonOutputParser(pydantic_object=AgentRecommendation)
        self.policy_text = self._load_policy()
    
    def _load_policy(self) -> str:
        """Load the policy document for this process."""
        base_path = Path(__file__).parent.parent.parent
        policy_path = base_path / "stop_reparto" / "policy_stop_reparto.txt"
        
        with open(policy_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_recommendation(
        self,
        messages: List[str],
        customer_context: Dict[str, Any],
        rules_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a structured recommendation for the customer service agent.
        
        Args:
            messages: Customer conversation messages
            customer_context: Customer data (plan, scoring, etc.)
            rules_decision: Decision from the rules engine (MANDATORY to follow)
            
        Returns:
            Structured recommendation dictionary
        """
        # Build conversation context
        conversation_text = "\n".join([f"Cliente: {msg}" for msg in messages])
        
        # Build system prompt with strict instructions
        system_prompt = f"""Eres un asistente experto para agentes de atención al cliente. Tu función es guiar al agente humano siguiendo ESTRICTAMENTE el manual operativo.

POLÍTICA Y PROCEDIMIENTOS:
{self.policy_text}

INSTRUCCIONES DE COMPORTAMIENTO:
1. PRIORIDAD DE RECONDUCCIÓN: Si el motivo es exceso de agua, empieza SIEMPRE por las opciones de reconducción (café, reducción, 11L, etc.) en el orden del manual.
2. DETECCIÓN DE RECHAZO (CRÍTICO): Si el cliente ya ha dicho "no", "ninguna", "quiero pararlo" o similar, la fase de alternativas se considera FINALIZADA. Pasa inmediatamente a la "QUINTA OPCIÓN" (Stop Cuota/0 euros) del manual. NO vuelvas a ofrecer alternativas ya rechazadas.
3. CONTRADICCIÓN REGLA/MANUAL: Aunque la REGLA DETERMINISTA diga `decision: reconduccion`, si el cliente ha rechazado las opciones en el chat, tu obligación es aplicar la lógica de CIERRE del manual. El manual manda sobre el proceso conversacional.
4. ADAPTACIÓN AL CANAL:
   - Si el canal es "Chat": Texto natural, sin rodeos, listo para pegar.
   - Si el canal es "Telefono": MÁXIMA BREVEDAD. Usa Bullet points Markdown cortos. Evita introducciones largas. Ve al grano: **Sondeo cortos** y **Alternativas directas**.
5. REGLA DE LÍMITES NUMÉRICOS (CRÍTICO): El manual permite un máximo de 2 stops al año. Si `stops_ultimo_ano` >= 2, NO puedes ofrecer ninguna modalidad de Stop (0€ o Cuota).
6. ACCIONES PERMITIDAS (VINCULANTE): Solo puedes ofrecer las acciones listadas en `allowed_actions` dentro de las REGLAS DETERMINISTAS. Si una acción no está en esa lista (ej: "stop_0euros"), tienes PROHIBIDO ofrecerla, aunque el cliente insista o el manual la mencione como posibilidad general. Las REGLAS DETERMINISTAS mandan sobre el manual.
7. CAMPO 'siguiente_paso': Solo la ruta técnica de Salesforce. Sin explicaciones adicionales.
8. TONO: Ultra-conciso. Elimina fórmulas de cortesía innecesarias si la charla ya ha empezado. Solo lo esencial para el agente.
9. CIERRE Y FCR: Si hay acuerdo, marca `gestion_finalizada: true`. Speech de cierre de 2 líneas máximo.

REGLAS DETERMINISTAS (OBLIGATORIAS):
{json.dumps(rules_decision, indent=2, ensure_ascii=False)}

FORMATO DE SALIDA OBLIGATORIO:
{self.parser.get_format_instructions()}

IMPORTANTE: Si el cliente ya aceptó, el 'titulo' debe ser "Gestión Completada con Éxito" y activa el flag `gestion_finalizada`."""

        # Build human prompt with all context
        human_prompt = f"""CONVERSACIÓN ACTUAL:
{conversation_text}

CONTEXTO DEL CLIENTE:
{json.dumps(customer_context, indent=2, ensure_ascii=False)}

Genera la recomendación estructurada para el canal {customer_context.get('canal', 'Chat')}. 
Si es Telefono, usa BULLET POINTS Markdown. 
Si es Chat, usa UN PÁRRAFO para copiar.
¿Se ha completado la gestión (el cliente aceptó)? Ajusta `gestion_finalizada`."""

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
                "titulo": "Error al generar recomendación",
                "objetivo": "Error",
                "stop_permitido": rules_decision.get("stop_allowed", False),
                "speech_sugerido": "Error en la generación. Por favor, revisa las reglas manualmente.",
                "siguiente_paso": "Contactar con soporte técnico",
                "error": str(e)
            }


def create_stop_reparto_agent(model_name: str = None) -> StopRepartoAgent:
    """
    Factory function to create a STOP_REPARTO specialist agent.
    
    Args:
        model_name: Optional model name override
        
    Returns:
        StopRepartoAgent instance
    """
    if model_name is None:
        model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash-exp")
    
    return StopRepartoAgent(model_name=model_name)
