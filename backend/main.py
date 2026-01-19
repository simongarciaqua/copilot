"""
Customer Service Copilot - FastAPI Backend
-------------------------------------------
Orchestrates the multi-agent pipeline:
1. Router agent detects process
2. Rules engine evaluates decision
3. Specialist agent generates recommendation
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rules_engine import load_rules_engine
from agents import create_router_agent, create_stop_reparto_agent


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
            if value and (current_val is None or current_val == "" or current_val == "null"):
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )


@app.get("/api/processes")
async def list_processes():
    """List available processes."""
    base_path = Path(__file__).parent.parent
    processes = []
    
    # Scan for process directories
    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name != 'backend' and item.name != 'frontend':
            rules_file = item / f"rules_{item.name}.json"
            if rules_file.exists():
                processes.append({
                    "name": item.name.upper(),
                    "has_rules": True,
                    "has_policy": (item / f"policy_{item.name}.txt").exists()
                })
    
    return {"processes": processes}


if __name__ == "__main__":
    import uvicorn
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY not set in environment")
        print("Please create a .env file with your API key")
    
    # Run server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
