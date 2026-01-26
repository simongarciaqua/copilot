from .router import RouterAgent
from .stop_reparto_agent import StopRepartoAgent
from .aviso_urgente_agent import AvisoUrgenteAgent

def create_router_agent():
    return RouterAgent()

def create_stop_reparto_agent():
    return StopRepartoAgent()

def create_aviso_urgente_agent():
    return AvisoUrgenteAgent()

__all__ = [
    "RouterAgent",
    "create_router_agent",
    "StopRepartoAgent",
    "create_stop_reparto_agent",
    "AvisoUrgenteAgent",
    "create_aviso_urgente_agent"
]
