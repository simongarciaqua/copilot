
from fastmcp import FastMCP
import httpx
import os

# Initialize FastMCP server
# This creates a FastAPI app internally that can be served via SSE
mcp = FastMCP("ElevenLabs Service")

@mcp.tool()
async def text_to_speech(text: str, voice_id: str = "JBFqnCBsd6RMkjVDRZzb") -> str:
    """
    Convert text to speech using ElevenLabs.
    Returns the path to the generated audio file.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return "Error: ELEVENLABS_API_KEY environment variable is not set."

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=headers, timeout=30.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            return f"Error contacting ElevenLabs: {str(e)}"

    # Save audio file to a static directory
    output_dir = os.path.join(os.getcwd(), "static", "audio")
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"speech_{os.urandom(4).hex()}.mp3"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, "wb") as f:
        f.write(response.content)
        
    return f"Audio generated successfully: {filepath}"

@mcp.tool()
async def get_voices() -> str:
    """
    List available voices from ElevenLabs.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return "Error: ELEVENLABS_API_KEY environment variable is not set."
        
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {"xi-api-key": api_key}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            return f"Error contacting ElevenLabs: {str(e)}"
            
    return response.text

if __name__ == "__main__":
    mcp.run(transport="sse")
