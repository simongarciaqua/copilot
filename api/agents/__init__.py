from .router import RouterAgent
from .stop_reparto_agent import StopRepartoAgent

def create_router_agent():
    return RouterAgent()

def create_stop_reparto_agent():
    return StopRepartoAgent()

__all__ = [
    "RouterAgent",
    "create_router_agent",
    "StopRepartoAgent",
    "create_stop_reparto_agent"
]
