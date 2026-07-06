"""Global node registry. Nodes self-register via the `@register` decorator.

The registry is the single catalogue the executor, the /api/nodes endpoint, and the
AI generator all read from.
"""

from __future__ import annotations

from app.core.errors import NotFoundError, ValidationError
from app.modules.nodes.base import Node


class NodeRegistry:
    def __init__(self) -> None:
        self._nodes: dict[str, type[Node]] = {}

    def register(self, node_cls: type[Node]) -> type[Node]:
        spec = getattr(node_cls, "spec", None)
        if spec is None:
            raise ValidationError(f"{node_cls.__name__} is missing a `spec`")
        if spec.type in self._nodes:
            raise ValidationError(f"Duplicate node type: {spec.type}")
        self._nodes[spec.type] = node_cls
        return node_cls

    def get(self, node_type: str) -> type[Node]:
        try:
            return self._nodes[node_type]
        except KeyError as exc:
            raise NotFoundError(f"Unknown node type: {node_type}") from exc

    def create(self, node_type: str) -> Node:
        return self.get(node_type)()

    def has(self, node_type: str) -> bool:
        return node_type in self._nodes

    def all_specs(self) -> list[dict]:
        """Serialised catalogue for the frontend and the AI generator."""
        out = []
        for cls in self._nodes.values():
            s = cls.spec
            out.append(
                {
                    "type": s.type,
                    "title": s.title,
                    "category": s.category,
                    "description": s.description,
                    "config_schema": s.config_schema,
                    "output_schema": s.output_schema,
                    "requires_connection": s.requires_connection,
                    "is_trigger": s.is_trigger,
                    "icon": s.icon,
                }
            )
        return out


registry = NodeRegistry()
