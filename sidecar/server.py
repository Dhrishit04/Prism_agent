import json
import logging
import os
from typing import Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from llm.openrouter import OpenRouterClient, DEFAULT_MODEL
from skills.registry import get_registry
from skills.skill_base import SkillResult
from voice import get_wake_word_skill, get_stt_skill, get_tts_skill, get_pipeline
from voice.wake_word import VOICE_DEPS_AVAILABLE

logger = logging.getLogger(__name__)

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


# --- Voice Pipeline Endpoints ---

class VoiceSettingsRequest(BaseModel):
    """Voice settings update request."""
    settings: dict


@app.on_event("startup")
async def init_voice_pipeline():
    """Initialize voice pipeline on startup."""
    settings = load_settings()
    voice_settings = settings.get("voice", {})

    if not VOICE_DEPS_AVAILABLE:
        logger.warning("Voice dependencies not available. Voice features disabled. Install with: pip install -e '.[voice]'")
        return

    # Initialize wake word skill
    wake_word_skill = get_wake_word_skill()
    wake_word_skill.load_settings(settings)

    # Initialize STT skill
    stt_skill = get_stt_skill()
    stt_skill.load_settings(settings)

    # Initialize TTS skill
    tts_skill = get_tts_skill()
    tts_skill.load_settings(settings)
    # Set OpenRouter client for TTS fallback
    client = get_client()
    tts_skill.set_openrouter_client(client)
    await tts_skill.initialize()

    # Initialize voice pipeline orchestrator
    pipeline = get_pipeline()
    pipeline.set_components(wake_word_skill, stt_skill, tts_skill)

    # Create LLM handler for the pipeline
    async def llm_handler(text: str) -> str:
        """Send text to LLM and return the full response."""
        client = get_client()
        if not client.api_key:
            return "Please configure your OpenRouter API key in Settings first."

        registry = get_skill_registry()
        tools = registry.get_tool_definitions()
        messages = [{"role": "user", "content": text}]
        result = await client.chat(messages, tools=tools)
        if result.get("error"):
            return f"Error: {result.get('message', 'Unknown error')}"
        return result["choices"][0]["message"].get("content", "")

    pipeline.set_llm_handler(llm_handler)


@app.get("/voice/status")
async def voice_status():
    """Get voice pipeline status."""
    settings = load_settings()
    wake_word_skill = get_wake_word_skill()
    wake_word_skill.load_settings(settings)
    stt_skill = get_stt_skill()
    stt_skill.load_settings(settings)
    tts_skill = get_tts_skill()
    tts_skill.load_settings(settings)
    pipeline = get_pipeline()

    return {
        "wake_word": wake_word_skill.get_status(),
        "stt": stt_skill.get_status(),
        "tts": tts_skill.get_status(),
        "pipeline": pipeline.get_status(),
        "enabled": settings.get("voice", {}).get("voice_enabled", False),
    }


@app.post("/voice/wake-word/start")
async def start_wake_word():
    """Start wake word detection."""
    settings = load_settings()
    wake_word_skill = get_wake_word_skill()
    wake_word_skill.load_settings(settings)

    if not settings.get("voice", {}).get("wake_word_enabled", False):
        return {"success": False, "error": "Wake word detection is disabled in settings"}

    result = await wake_word_skill.start_listening()
    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/wake-word/stop")
async def stop_wake_word():
    """Stop wake word detection."""
    wake_word_skill = get_wake_word_skill()
    result = await wake_word_skill.stop_listening()
    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/stt/transcribe")
async def stt_transcribe(request: dict):
    """Transcribe audio file or start/stop recording."""
    audio_path = request.get("audio_path")
    settings = load_settings()
    stt_skill = get_stt_skill()
    stt_skill.load_settings(settings)

    if audio_path:
        result = await stt_skill.transcribe(audio_path=audio_path)
    else:
        result = await stt_skill.transcribe()

    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/stt/start")
async def stt_start_recording():
    """Start recording for STT."""
    settings = load_settings()
    stt_skill = get_stt_skill()
    stt_skill.load_settings(settings)

    result = await stt_skill.start_recording()
    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/stt/stop")
async def stt_stop_recording():
    """Stop recording and transcribe."""
    settings = load_settings()
    stt_skill = get_stt_skill()
    stt_skill.load_settings(settings)

    result = await stt_skill.stop_recording()
    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/tts/speak")
async def tts_speak(request: dict):
    """Speak text using TTS."""
    text = request.get("text", "")
    if not text:
        return {"success": False, "error": "Text is required"}

    settings = load_settings()
    tts_skill = get_tts_skill()
    tts_skill.load_settings(settings)
    # Ensure OpenRouter client is set
    client = get_client()
    tts_skill.set_openrouter_client(client)

    result = await tts_skill.speak(text)
    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/tts/stop")
async def tts_stop():
    """Stop current TTS playback."""
    settings = load_settings()
    tts_skill = get_tts_skill()
    tts_skill.load_settings(settings)

    result = await tts_skill.stop()
    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/settings")
async def update_voice_settings(request: VoiceSettingsRequest):
    """Update voice settings."""
    settings = load_settings()
    if "voice" not in settings:
        settings["voice"] = {}
    settings["voice"].update(request.settings)

    # Save settings
    path = get_settings_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(settings, f, indent=2)

    # Reload voice skills with new settings
    wake_word_skill = get_wake_word_skill()
    wake_word_skill.load_settings(settings)
    stt_skill = get_stt_skill()
    stt_skill.load_settings(settings)
    tts_skill = get_tts_skill()
    tts_skill.load_settings(settings)
    client = get_client()
    tts_skill.set_openrouter_client(client)
    await tts_skill.initialize()

    return {"success": True, "settings": settings["voice"]}


# --- Voice Pipeline Orchestration Endpoints ---

@app.post("/voice/pipeline/start")
async def start_voice_pipeline():
    """Start the full voice pipeline (wake word → STT → LLM → TTS loop)."""
    settings = load_settings()
    if not settings.get("voice", {}).get("voice_enabled", False):
        return {"success": False, "error": "Voice is disabled in settings"}

    pipeline = get_pipeline()
    result = await pipeline.start()
    return {"success": result.success, "data": result.data, "error": result.error}


@app.post("/voice/pipeline/stop")
async def stop_voice_pipeline():
    """Stop the voice pipeline."""
    pipeline = get_pipeline()
    result = await pipeline.stop()
    return {"success": result.success, "data": result.data, "error": result.error}


@app.get("/voice/pipeline/status")
async def voice_pipeline_status():
    """Get voice pipeline orchestrator status."""
    pipeline = get_pipeline()
    return pipeline.get_status()