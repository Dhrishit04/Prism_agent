import json
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llm.openrouter import OpenRouterClient, DEFAULT_MODEL

app = FastAPI(title="Prism Sidecar", version="0.1.0")
_client: Optional[OpenRouterClient] = None


def get_settings_path() -> str:
    """Get the path to the settings file."""
    home = os.path.expanduser("~")
    return os.path.join(home, ".prism", "settings.json")


def load_settings() -> dict:
    """Load settings from the config file."""
    path = get_settings_path()
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_client() -> OpenRouterClient:
    global _client
    if _client is None:
        # Try to load API key from settings
        settings = load_settings()
        api_key = settings.get("openrouter_api_key", "")
        _client = OpenRouterClient(api_key=api_key)
    return _client


class HealthResponse(BaseModel):
    status: str
    version: str


class MessageRequest(BaseModel):
    message: str
    model: str = DEFAULT_MODEL
    history: list[dict] = []


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/chat/stream")
async def chat_stream(request: MessageRequest):
    """Stream a chat response from OpenRouter."""
    client = get_client()
    if not client.api_key:
        # No API key configured — echo mode
        async def echo():
            yield f"data: {json.dumps({'content': 'Please configure your OpenRouter API key in Settings first.'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(echo(), media_type="text/event-stream")

    messages = request.history + [{"role": "user", "content": request.message}]

    async def generate():
        async for chunk in client.chat_stream(messages, model=request.model):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/chat")
async def chat(request: MessageRequest):
    """Non-streaming chat (fallback)."""
    client = get_client()
    if not client.api_key:
        return {"response": "Please configure your OpenRouter API key in Settings first."}

    messages = request.history + [{"role": "user", "content": request.message}]
    result = await client.chat(messages, model=request.model)
    if result.get("error"):
        raise HTTPException(status_code=502, detail=result.get("message"))
    content = result["choices"][0]["message"]["content"]
    return {"response": content}


@app.get("/models")
async def list_models():
    """List available OpenRouter models."""
    client = get_client()
    if not client.api_key:
        return {"models": []}
    models = await client.list_models()
    return {"models": models}


@app.post("/configure")
async def configure(data: dict):
    """Set API key and reconfigure the client."""
    global _client
    api_key = data.get("api_key", "")
    _client = OpenRouterClient(api_key=api_key)
    return {"status": "ok"}


@app.get("/settings")
async def get_settings():
    """Get current settings from the config file."""
    return load_settings()