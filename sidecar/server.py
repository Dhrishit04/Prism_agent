from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="Prism Sidecar", version="0.1.0")


class HealthResponse(BaseModel):
    status: str
    version: str


class MessageRequest(BaseModel):
    message: str
    model: str = "anthropic/claude-3.5-sonnet"


class MessageResponse(BaseModel):
    response: str


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    # TODO: Phase 3 — integrate with OpenRouter
    return MessageResponse(response=f"Echo: {request.message}")


@app.get("/models")
async def list_models():
    # TODO: Phase 3 — fetch from OpenRouter API
    return {
        "models": [
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet"},
            {"id": "openai/gpt-4o", "name": "GPT-4o"},
        ]
    }