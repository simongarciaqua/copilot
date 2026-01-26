"""
Customer Service Copilot - FastAPI Backend
-------------------------------------------
Orchestrates the multi-agent pipeline:
1. Router agent detects process
2. Rules engine evaluates decision
3. Specialist agent generates recommendation
"""

import os
import sys
from pathlib import Path

# Path hack for Vercel imports
current_dir = Path(__file__).parent.resolve()
parent_dir = current_dir.parent.resolve()

if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Debug info for Vercel logs
print(f"DEBUG: Python Path: {sys.path}")
print(f"DEBUG: Current Dir: {current_dir}")

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rules_engine import load_rules_engine
from agents import create_router_agent, create_stop_reparto_agent, create_aviso_urgente_agent


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request model for conversation analysis."""
    messages: List[str] = Field(description="List of customer messages")
    customer_context: Dict[str, Any] = Field(description="Customer context data")


class AnalyzeResponse(BaseModel):
    """Response model for analysis results."""
    status: str = Field(description="System state: NEED_INFO or RECOMMENDATION")
    process: str = Field(description="Detected process")
    confidence: float = Field(description="Detection confidence")
    rules_decision: Dict[str, Any] = Field(description="Rules engine decision or missing info requirement")
    recommendation: Optional[Dict[str, Any]] = Field(default=None, description="Agent recommendation (only if status is RECOMMENDATION)")
    enriched_context: Optional[Dict[str, Any]] = Field(default=None, description="The customer context after LLM extraction")


# Initialize FastAPI app
app = FastAPI(
    title="Customer Service Copilot API",
    description="Internal copilot for customer service agents",
    version="1.1.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for local dev stability
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize agents
router_agent = None
stop_reparto_agent = None


def get_router_agent():
    """Get or create router agent (lazy initialization)."""
    global router_agent
    if router_agent is None:
        router_agent = create_router_agent()
    return router_agent


def get_stop_reparto_agent():
    """Get or create STOP_REPARTO agent (lazy initialization)."""
    global stop_reparto_agent
    if stop_reparto_agent is None:
        stop_reparto_agent = create_stop_reparto_agent()
    return stop_reparto_agent


# Initialize Aviso Urgente agent
aviso_urgente_agent = None

def get_aviso_urgente_agent():
    """Get or create AVISO_URGENTE agent (lazy initialization)."""
    global aviso_urgente_agent
    if aviso_urgente_agent is None:
        aviso_urgente_agent = create_aviso_urgente_agent()
    return aviso_urgente_agent


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.1.0",
        "gemini_configured": bool(os.getenv("GOOGLE_API_KEY"))
    }


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_conversation(request: AnalyzeRequest):
    """
    Analyze a customer conversation and generate recommendations.
    
    1. Router detects process
    2. Check for required info
    3. If info missing -> return status: NEED_INFO
    4. If info present -> evaluate rules -> Specialist Agent -> status: RECOMMENDATION
    """
    try:
        # Validate input
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        if not request.customer_context:
            raise HTTPException(status_code=400, detail="No customer context provided")
        
        # Step 1: Detect process and extract data using router agent
        router = get_router_agent()
        detection = router.detect_process(request.messages)
        
        process_name = detection.get("process", "UNKNOWN")
        confidence = detection.get("confidence", 0.0)
        extracted_data = detection.get("extracted_data", {})
        
        # Unir contexto estático con datos extraídos dinámicamente
        enriched_context = request.customer_context.copy()
        for key, value in extracted_data.items():
            current_val = enriched_context.get(key)
            # Actualizamos si el valor extraído no es nulo y el actual está vacío o es nulo
            if value is not None and (current_val is None or current_val == "" or current_val == "null"):
                enriched_context[key] = value

        # CASO ESPECIAL: Si es charla social (SmallTalk), no lanzamos error ni evaluamos reglas
        if process_name == "SOCIAL":
            return AnalyzeResponse(
                status="SOCIAL",
                process="SOCIAL",
                confidence=confidence,
                rules_decision={"status": "SOCIAL", "message": "Conversación social detectada"},
                recommendation=None,
                enriched_context=enriched_context
            )

        if process_name == "UNKNOWN" or confidence < 0.3: # Bajamos umbral para charla
             return AnalyzeResponse(
                status="UNKNOWN",
                process="UNKNOWN",
                confidence=confidence,
                rules_decision={"status": "UNKNOWN", "message": "Esperando solicitud de negocio..."},
                recommendation=None,
                enriched_context=enriched_context
            )
        
        # Step 2: Load rules engine for detected process
        try:
            rules_engine = load_rules_engine(process_name)
        except FileNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Rules not found for process: {process_name}"
            )
        
        # Step 3: Evaluate rules (ahora con el contexto enriquecido por el LLM)
        rules_output = rules_engine.evaluate(enriched_context)
        status = rules_output.get("status", "RECOMMENDATION")
        
        # Step 4: Branch based on status
        if status == "NEED_INFO":
            return AnalyzeResponse(
                status="NEED_INFO",
                process=process_name,
                confidence=confidence,
                rules_decision=rules_output,
                recommendation=None,
                enriched_context=enriched_context
            )
        
        # Step 5: Generate recommendation using specialist agent
        if process_name == "STOP_REPARTO":
            agent = get_stop_reparto_agent()
            recommendation = agent.generate_recommendation(
                messages=request.messages,
                customer_context=enriched_context,
                rules_decision=rules_output
            )
        elif process_name == "AVISO_URGENTE":
            agent = get_aviso_urgente_agent()
            recommendation = agent.generate_recommendation(
                messages=request.messages,
                customer_context=enriched_context,
                rules_decision=rules_output
            )
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Specialist agent not implemented for process: {process_name}"
            )
        
        # Return complete RECOMMENDATION analysis
        return AnalyzeResponse(
            status="RECOMMENDATION",
            process=process_name,
            confidence=confidence,
            rules_decision=rules_output,
            recommendation=recommendation,
            enriched_context=enriched_context
        )
    
    except HTTPException as he:
        # Re-raise HTTP exceptions so FastAPI handles them (returns JSON)
        raise he
    except Exception as e:
        import traceback
        error_msg = f"Internal Server Error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg) # Log to Vercel console
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(e),
                "trace": traceback.format_exc()
            }
        )


@app.get("/api/processes")
async def list_processes():
    """List available processes."""
    base_path = Path(__file__).parent
    processes = []
    
    # Scan for process directories
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name not in ['agents', 'rules_engine', 'stop_reparto']:
            # Maybe it's a new process folder?
            pass
            
    # Always include STOP_REPARTO if it exists
    if (base_path / "stop_reparto").exists():
        processes.append({
            "name": "STOP_REPARTO",
            "has_rules": True,
            "has_policy": True
        })
    
    if (base_path / "aviso_urgente").exists():
        processes.append({
            "name": "AVISO_URGENTE",
            "has_rules": True,
            "has_policy": True
        })
    
    return {"processes": processes}


class TTSRequest(BaseModel):
    text: str
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb" # Default voice if not specified


@app.post("/api/tts")
async def text_to_speech_proxy(request: TTSRequest):
    """
    Proxy endpoint for ElevenLabs Text-to-Speech to keep API key secure.
    Returns audio/mpeg stream.
    """
    import httpx
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ElevenLabs API Key not configured")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{request.voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": request.text,
        "model_id": "eleven_multilingual_v2", # Better for Spanish
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    # We need a synchronous-looking response for streaming, or just return content for simplicity in POC.
    # For a simple widget, returning bytes is fine.
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers, timeout=30.0)
            response.raise_for_status()
            
            from fastapi.responses import Response
            return Response(content=response.content, media_type="audio/mpeg")
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"ElevenLabs Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY not set in environment")
        print("Please create a .env file with your API key")
    
    # Run server
    uvicorn.run(
        "index:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
