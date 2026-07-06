"""AI provider abstraction.

We normalise providers through LiteLLM, then wrap it in OUR service. The wrapper —
not LiteLLM — is where product concerns live: model routing, per-user metering,
and structured (JSON-schema-constrained) output. The rest of the app depends only
on these `AIRequest`/`AIResponse` shapes, so swapping providers never touches
callers. Users bring their own API keys in MVP.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class AIRequest:
    prompt: str
    system: str | None = None
    model: str = "gemini/gemini-1.5-flash"
    temperature: float = 0.4
    max_tokens: int = 1024
    # When set, the model is forced to return JSON validating against this schema.
    json_schema: dict[str, Any] | None = None
    api_key: str | None = None  # resolved from the user's connection/vault


@dataclass
class AIResponse:
    text: str
    data: dict[str, Any] | None = None  # parsed JSON when json_schema was requested
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)


class AIProvider(Protocol):
    async def complete(self, req: AIRequest) -> AIResponse: ...


class LiteLLMProvider:
    """Real provider. Imported lazily so tests/local dev don't require the dep."""

    async def complete(self, req: AIRequest) -> AIResponse:
        import litellm

        messages = []
        if req.system:
            messages.append({"role": "system", "content": req.system})
        messages.append({"role": "user", "content": req.prompt})

        kwargs: dict[str, Any] = {
            "model": req.model,
            "messages": messages,
            "temperature": req.temperature,
            "max_tokens": req.max_tokens,
        }
        if req.api_key:
            kwargs["api_key"] = req.api_key
        if req.json_schema is not None:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await litellm.acompletion(**kwargs)
        text = resp["choices"][0]["message"]["content"] or ""
        data = _safe_json(text) if req.json_schema is not None else None
        usage = dict(resp.get("usage", {}) or {})
        return AIResponse(text=text, data=data, model=req.model, usage=usage)


class AIService:
    """The dependency callers use. Add metering/rate-limit hooks here."""

    def __init__(self, provider: AIProvider):
        self._provider = provider

    async def generate(self, req: AIRequest) -> AIResponse:
        # TODO(metering): record usage per user_id, enforce quotas.
        return await self._provider.complete(req)


def _safe_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Best-effort: extract first {...} block.
        start, end = text.find("{"), text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None
