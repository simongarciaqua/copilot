
import os
import httpx
import json
import uuid
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
from pathlib import Path

# Import logic from the project
# We need to add the parent directory to path since we are in 'api' usually
import sys
sys.path.append(os.getcwd())

from index import analyze_conversation, AnalyzeRequest

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "ok", "mcp_endpoint": "/sse"}

@app.get("/sse")
async def sse_endpoint(request: Request):
    async def event_generator():
        session_id = str(uuid.uuid4()).replace("-", "")
        # The 'endpoint' event tells the client where to send POST messages
        yield f"event: endpoint\ndata: /messages/{session_id}\n\n"
        
        while True:
            if await request.is_disconnected():
                break
            yield ":\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/messages/{session_id}")
async def handle_messages(session_id: str, request: Request):
    payload = await request.json()
    msg_id = payload.get("id")
    method = payload.get("method")
    params = payload.get("params", {})
    
    # Standard MCP Handshake
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05", # Current MCP version
                "capabilities": {
                    "tools": {},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "Aquaservice-Copilot-Knowledge",
                    "version": "1.1.0"
                }
            }
        }
    
    if method == "notifications/initialized":
        return None

    # Tools List: Exposing the "Knowledge" of the project
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "tools": [
                    {
                        "name": "analyze_customer_case",
                        "description": "Analiza una conversación con un cliente de Aquaservice (Stop Reparto o Aviso Urgente) y devuelve la mejor recomendación basada en las reglas oficiales.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "messages": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "Lista de mensajes recientes del cliente"
                                },
                                "plan": {
                                    "type": "string", 
                                    "enum": ["Ahorro", "Planocho"],
                                    "description": "Plan contratado por el cliente"
                                },
                                "scoring": {
                                    "type": "number",
                                    "description": "Puntuación de fidelidad del cliente (1-5)"
                                },
                                "canal": {
                                    "type": "string",
                                    "enum": ["Telefono", "Chat"],
                                    "description": "Canal de atención"
                                }
                            },
                            "required": ["messages"]
                        }
                    }
                ]
            }
        }

    # Tool Execution
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        if tool_name == "analyze_customer_case":
            # Call the existing FastAPI logic internally
            messages = args.get("messages", [])
            # Prepare context (defaulting if not provided)
            context = {
                "plan": args.get("plan", "Ahorro"),
                "scoring": args.get("scoring", 3.0),
                "canal": args.get("canal", "Telefono"),
                "stops_ultimo_ano": 0,
                "albaran_descargado": False,
                "tipo_cliente": "residencial",
                "is_delivery_day": False,
                "has_pending_usual_delivery": False
            }
            
            try:
                # We mock the AnalyzeRequest to reuse the logic in index.py
                from pydantic import ValidationError
                req = AnalyzeRequest(messages=messages, customer_context=context)
                result = await analyze_conversation(req)
                
                # Format response for MCP
                response_text = f"PROCESO DETECTADO: {result.process}\n\n"
                if result.recommendation:
                    response_text += f"TÍTULO: {result.recommendation['titulo']}\n"
                    response_text += f"RECOMENDACIÓN:\n{result.recommendation['speech_sugerido']}\n\n"
                    response_text += f"SIGUIENTE PASO CRM: {result.recommendation['siguiente_paso']}"
                else:
                    response_text += "No se pudo generar una recomendación completa. "
                    if result.rules_decision and "message" in result.rules_decision:
                        response_text += result.rules_decision["message"]
                
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": response_text}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error procesando el caso: {str(e)}"}],
                        "isError": True
                    }
                }

    # Default fallback
    return {"jsonrpc": "2.0", "id": msg_id, "result": {}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
