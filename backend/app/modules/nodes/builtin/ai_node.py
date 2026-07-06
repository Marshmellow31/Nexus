"""AI generation node. One action among many — provider-agnostic via AIService."""

from __future__ import annotations

from typing import Any

from app.modules.ai.service import AIRequest
from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


@registry.register
class AIGenerateNode(Node):
    spec = NodeSpec(
        type="ai.generate",
        title="AI",
        category="ai",
        description="Generate text (or structured JSON) from a prompt using an AI model.",
        icon="sparkles",
        config_schema={
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "title": "Prompt",
                    "description": "Supports {{ nodes.<id>.output.<path> }} templates.",
                    "x-widget": "textarea",
                },
                "system": {"type": "string", "title": "System instructions"},
                "model": {
                    "type": "string",
                    "title": "Model",
                    "default": "gpt-4o-mini",
                    "enum": ["gpt-4o-mini", "gpt-4o", "gemini/gemini-1.5-flash"],
                },
                "temperature": {
                    "type": "number",
                    "title": "Temperature",
                    "default": 0.4,
                    "minimum": 0,
                    "maximum": 2,
                },
            },
            "required": ["prompt"],
        },
        output_schema={
            "type": "object",
            "properties": {"text": {"type": "string"}},
        },
    )

    async def execute(
        self, ctx: ExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        resp = await ctx.services.ai.generate(
            AIRequest(
                prompt=config["prompt"],
                system=config.get("system"),
                model=config.get("model", "gpt-4o-mini"),
                temperature=float(config.get("temperature", 0.4)),
            )
        )
        return {"text": resp.text, "model": resp.model, "usage": resp.usage}
