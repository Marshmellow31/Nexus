"""Delay node. MVP: inline async sleep bounded by settings.delay_inline_max_seconds.
Longer delays (durable resume via `resume_at`) are a documented v1.1 follow-up."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import settings
from app.core.errors import ValidationError
from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


@registry.register
class DelayNode(Node):
    spec = NodeSpec(
        type="logic.delay",
        title="Delay",
        category="logic",
        description="Pause the workflow for a number of seconds before continuing.",
        icon="clock",
        config_schema={
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "integer",
                    "title": "Seconds",
                    "default": 5,
                    "minimum": 1,
                    "maximum": settings.delay_inline_max_seconds,
                }
            },
            "required": ["seconds"],
        },
        output_schema={"type": "object", "properties": {"waited": {"type": "integer"}}},
    )

    async def execute(
        self, ctx: ExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        seconds = int(config.get("seconds", 5))
        if seconds > settings.delay_inline_max_seconds:
            raise ValidationError(
                f"Delay exceeds inline limit of {settings.delay_inline_max_seconds}s "
                "(durable long delays are not yet supported)"
            )
        await asyncio.sleep(seconds)
        return {"waited": seconds}
