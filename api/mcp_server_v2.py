
import os
import httpx
from mcp.server.fastapi import Iceberg # Wait, checking correct import
import os
import httpx
from fastapi import FastAPI
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent
from starlette.middleware.cors import CORSMiddleware

# Initialize MCP Server
app = FastAPI(title="ElevenLabs MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

server = Server("ElevenLabs Service")

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="text_to_speech",
            description="Convert text to speech using ElevenLabs. Returns the path to the generated audio file.",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "voice_id": {"type": "string", "default": "JBFqnCBsd6RMkjVDRZzb"}
                },
                "required": ["text"]
            },
        ),
        Tool(
            name="get_voices",
            description="List available voices from ElevenLabs.",
            inputSchema={"type": "object", "properties": {}},
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle tool calls."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return [TextContent(type="text", text="Error: ELEVENLABS_API_KEY not set.")]

    if name == "get_voices":
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": api_key}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            return [TextContent(type="text", text=resp.text)]

    elif name == "text_to_speech":
        text = arguments.get("text")
        voice_id = arguments.get("voice_id", "JBFqnCBsd6RMkjVDRZzb")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"Accept": "audio/mpeg", "Content-Type": "application/json", "xi-api-key": api_key}
        data = {"text": text, "model_id": "eleven_monolingual_v1"}
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=data, headers=headers)
            if resp.status_code != 200:
                return [TextContent(type="text", text=f"Error: {resp.text}")]
            
            output_dir = os.path.join(os.getcwd(), "static", "audio")
            os.makedirs(output_dir, exist_ok=True)
            filename = f"speech_{os.urandom(4).hex()}.mp3"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return [TextContent(type="text", text=f"Audio generated: {filepath}")]
    
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

sse = SseServerTransport("/messages")

@app.get("/sse")
async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request.send) as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

@app.post("/messages")
async def handle_messages(request):
    await sse.handle_post_message(request.scope, request.receive, request.send)

# Add a redirect from / to /sse to handle tracers
@app.get("/")
async def root():
    return {"status": "ok", "mcp_endpoint": "/sse"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
