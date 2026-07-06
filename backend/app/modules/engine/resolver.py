"""Template resolution: `{{ nodes.<id>.output.<path> }}` and `{{ trigger.<path> }}`.

Deliberately NOT a general expression language. It is pure, data-only path lookup —
no eval, no Jinja, no attribute access on Python objects — so a malicious workflow
config cannot execute code. This is a security boundary.
"""

from __future__ import annotations

import re
from typing import Any

_TEMPLATE = re.compile(r"\{\{\s*(?P<expr>[^}]+?)\s*\}\}")


class TemplateResolver:
    def resolve(
        self,
        config: Any,
        node_outputs: dict[str, dict[str, Any]],
        trigger_payload: dict[str, Any],
    ) -> Any:
        root = {"nodes": _wrap_outputs(node_outputs), "trigger": trigger_payload}
        return self._walk(config, root)

    def _walk(self, value: Any, root: dict[str, Any]) -> Any:
        if isinstance(value, str):
            return self._render_string(value, root)
        if isinstance(value, dict):
            return {k: self._walk(v, root) for k, v in value.items()}
        if isinstance(value, list):
            return [self._walk(v, root) for v in value]
        return value

    def _render_string(self, text: str, root: dict[str, Any]) -> Any:
        # If the whole string is a single template, preserve the resolved type
        # (e.g. a dict or number rather than its string form).
        whole = _TEMPLATE.fullmatch(text.strip())
        if whole:
            return _lookup(whole.group("expr"), root)

        def repl(m: re.Match[str]) -> str:
            val = _lookup(m.group("expr"), root)
            return "" if val is None else str(val)

        return _TEMPLATE.sub(repl, text)


def _wrap_outputs(node_outputs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    # Expose as nodes.<id>.output.<...>
    return {node_id: {"output": out} for node_id, out in node_outputs.items()}


def _lookup(expr: str, root: dict[str, Any]) -> Any:
    parts = [p.strip() for p in expr.split(".") if p.strip()]
    current: Any = root
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
        if current is None:
            return None
    return current
