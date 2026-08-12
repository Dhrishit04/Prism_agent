import json
import os
from typing import Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm.openrouter import OpenRouterClient, DEFAULT_MODEL
from skills.registry import get_registry
from skills.skill_base import SkillResult

app = FastAPI(title="Prism Sidecar", version="0.1.0")
_client: Optional[OpenRouterClient] = None
_registry = None


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


def get_skill_registry():
    """Get or initialize the skill registry."""
    global _registry
    if _registry is None:
        _registry = get_registry()
        _registry.load_skills()
    return _registry


class HealthResponse(BaseModel):
    status: str
    version: str


class MessageRequest(BaseModel):
    message: str
    model: str = DEFAULT_MODEL
    history: list[dict] = []


class SkillExecuteRequest(BaseModel):
    skill_name: str
    parameters: dict = {}


@app.on_event("startup")
async def startup_event():
    """Initialize skill registry on startup."""
    get_skill_registry()


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="0.1.0")


@app.post("/chat/stream")
async def chat_stream(request: MessageRequest):
    """Stream a chat response from OpenRouter with skill tool calling."""
    client = get_client()
    if not client.api_key:
        # No API key configured — echo mode
        async def echo():
            yield f"data: {json.dumps({'content': 'Please configure your OpenRouter API key in Settings first.'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(echo(), media_type="text/event-stream")

    # Get skill tool definitions
    registry = get_skill_registry()
    tools = registry.get_tool_definitions()

    messages = request.history + [{"role": "user", "content": request.message}]

    async def generate() -> AsyncGenerator[str, None]:
        """Generate streaming response with tool calling loop."""
        # Track tool calls we need to execute
        pending_tool_calls: list[dict] = []
        current_tool_call: dict | None = None
        buffer = ""

        async def execute_tool_calls(tool_calls: list[dict]) -> list[dict]:
            """Execute a batch of tool calls and return tool result messages."""
            results = []
            for tc in tool_calls:
                function = tc.get("function", {})
                name = function.get("name", "")
                args_str = function.get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {}

                # Execute the skill
                result = await registry.execute_skill(name, **args)

                # Format as tool result message
                tool_result = {
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "name": name,
                    "content": json.dumps({
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                    }),
                }
                results.append(tool_result)
            return results

        # Start the first turn with user message
        turn_messages = messages
        turn_count = 0
        max_turns = 10  # Prevent infinite loops

        while turn_count < max_turns:
            turn_count += 1
            pending_tool_calls = []
            current_tool_call = None
            buffer = ""

            # Stream this turn
            async for chunk in client.chat_stream(turn_messages, model=request.model, tools=tools):
                if chunk.startswith("data: "):
                    data = chunk[6:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        parsed = json.loads(data)
                        # Yield content to frontend
                        if parsed.get("content"):
                            yield f"data: {json.dumps({'content': parsed['content']})}\n\n"
                        # Buffer tool calls
                        if parsed.get("tool_calls"):
                            for tc in parsed["tool_calls"]:
                                # Tool calls come in streaming chunks; we need to accumulate them
                                index = tc.get("index", 0)
                                while len(pending_tool_calls) <= index:
                                    pending_tool_calls.append({"id": "", "type": "function", "function": {"name": "", "arguments": ""}})
                                call = pending_tool_calls[index]
                                if tc.get("id"):
                                    call["id"] = tc["id"]
                                if tc.get("type"):
                                    call["type"] = tc["type"]
                                func = tc.get("function", {})
                                if func.get("name"):
                                    call["function"]["name"] = func["name"]
                                if func.get("arguments"):
                                    call["function"]["arguments"] += func["arguments"]
                    except json.JSONDecodeError:
                        continue

            # After stream ends, check if we have tool calls to execute
            complete_tool_calls = [tc for tc in pending_tool_calls if tc.get("function", {}).get("name")]

            if not complete_tool_calls:
                # No tool calls - we're done
                break

            # Execute tool calls
            tool_results = await execute_tool_calls(complete_tool_calls)

            # Add assistant message with tool_calls and tool results to conversation
            turn_messages = turn_messages + [
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": complete_tool_calls,
                }
            ] + tool_results

            # Continue loop - LLM will respond to tool results

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/chat")
async def chat(request: MessageRequest):
    """Non-streaming chat (fallback) with skill tools."""
    client = get_client()
    if not client.api_key:
        return {"response": "Please configure your OpenRouter API key in Settings first."}

    # Get skill tool definitions
    registry = get_skill_registry()
    tools = registry.get_tool_definitions()

    messages = request.history + [{"role": "user", "content": request.message}]
    result = await client.chat(messages, model=request.model, tools=tools)
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


# --- Skill System Endpoints ---

@app.get("/skills")
async def list_skills():
    """List all available skills with their definitions."""
    registry = get_skill_registry()
    skills = registry.get_all_skills()
    return {
        "skills": [
            {
                "name": skill.name,
                "description": skill.description,
                "parameters": skill.parameters,
            }
            for skill in skills.values()
        ]
    }


@app.get("/skills/tools")
async def get_skill_tools():
    """Get all skills as OpenAI-compatible tool definitions."""
    registry = get_skill_registry()
    return {"tools": registry.get_tool_definitions()}


@app.post("/skills/execute")
async def execute_skill(request: SkillExecuteRequest):
    """Execute a skill by name with parameters."""
    registry = get_skill_registry()
    result = await registry.execute_skill(request.skill_name, **request.parameters)

    if isinstance(result, dict) and "success" in result:
        return result
    # Handle SkillResult dataclass
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
    }


@app.post("/skills/reload")
async def reload_skills():
    """Reload all skills (useful for development)."""
    registry = get_skill_registry()
    skills = registry.reload()
    return {
        "status": "reloaded",
        "skills": list(skills.keys()),
    }