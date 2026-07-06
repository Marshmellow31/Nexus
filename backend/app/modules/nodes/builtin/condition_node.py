"""Condition (branch) node. Emits {"result": bool}; the executor prunes the
untaken "true"/"false" edge. Comparison is data-only — no eval."""

from __future__ import annotations

from typing import Any

from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry

def _loose_eq(a: Any, b: Any) -> bool:
    """Config values are always strings, but templates resolve to native types —
    compare numerically when both sides parse as numbers, else as strings."""
    if a == b:
        return True
    na, nb = _num(a), _num(b)
    if na == na and nb == nb:  # neither is NaN
        return na == nb
    return str(a) == str(b)


_OPS = {
    "eq": _loose_eq,
    "ne": lambda a, b: not _loose_eq(a, b),
    "gt": lambda a, b: _num(a) > _num(b),
    "gte": lambda a, b: _num(a) >= _num(b),
    "lt": lambda a, b: _num(a) < _num(b),
    "lte": lambda a, b: _num(a) <= _num(b),
    "contains": lambda a, b: str(b) in str(a),
    "is_empty": lambda a, _b: a in (None, "", [], {}),
    "is_truthy": lambda a, _b: bool(a),
}


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return float("nan")


@registry.register
class ConditionNode(Node):
    spec = NodeSpec(
        type="logic.condition",
        title="Condition",
        category="logic",
        description="Branch the workflow. Connect the true/false handles to different paths.",
        icon="git-branch",
        config_schema={
            "type": "object",
            "properties": {
                "left": {"type": "string", "title": "Value", "description": "Templated."},
                "operator": {
                    "type": "string",
                    "title": "Operator",
                    "default": "eq",
                    "enum": list(_OPS.keys()),
                },
                "right": {"type": "string", "title": "Compare to"},
            },
            "required": ["left", "operator"],
        },
        output_schema={
            "type": "object",
            "properties": {"result": {"type": "boolean"}},
        },
    )

    async def execute(
        self, ctx: ExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        op = _OPS[config.get("operator", "eq")]
        result = bool(op(config.get("left"), config.get("right")))
        return {"result": result}
