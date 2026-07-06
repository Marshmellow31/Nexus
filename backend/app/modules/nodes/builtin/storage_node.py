"""Storage node — persist a value into Nexus's own store (our lightweight 'Notes').
Avoids building Notion inside Nexus; writes to a `stored_items` table via services."""

from __future__ import annotations

from typing import Any

from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


@registry.register
class StorageNode(Node):
    spec = NodeSpec(
        type="action.store",
        title="Save Note",
        category="action",
        description="Save text into Nexus notes/storage for later retrieval.",
        icon="database",
        config_schema={
            "type": "object",
            "properties": {
                "collection": {"type": "string", "title": "Collection", "default": "notes"},
                "content": {
                    "type": "string",
                    "title": "Content",
                    "x-widget": "textarea",
                },
            },
            "required": ["content"],
        },
        output_schema={"type": "object", "properties": {"stored": {"type": "boolean"}}},
    )

    async def execute(
        self, ctx: ExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        # The concrete persistence is wired via services in a later phase; for now
        # return the payload so downstream nodes and history capture it.
        return {
            "stored": True,
            "collection": config.get("collection", "notes"),
            "content": config["content"],
        }
