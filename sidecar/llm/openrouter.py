"""OpenRouter LLM client with streaming support."""

import json
from typing import AsyncGenerator

import httpx

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"


class OpenRouterClient:
    def __init__(self, api_key: str, base_url: str = OPENROUTER_BASE):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://prism.ai",
            "X-Title": "Prism AI Agent",
        }

    async def chat_stream(
        self, messages: list[dict], model: str = DEFAULT_MODEL
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from OpenRouter. Yields content deltas."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": True,
                },
            ) as response:
                if response.status_code != 200:
                    error_body = await response.aread()
                    yield json.dumps({
                        "error": True,
                        "message": f"OpenRouter error {response.status_code}: {error_body.decode()}",
                    })
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield json.dumps({"content": content})
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> list[dict]:
        """Fetch available models from OpenRouter."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/models",
                headers=self.headers,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            return []

    async def chat(
        self, messages: list[dict], model: str = DEFAULT_MODEL
    ) -> dict:
        """Non-streaming chat completion."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                },
            )
            if response.status_code != 200:
                return {
                    "error": True,
                    "message": f"OpenRouter error {response.status_code}: {response.text}",
                }
            return response.json()