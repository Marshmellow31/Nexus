"""Node subsystem.

Import side effects register every built-in node into the global registry.
`register_builtin_nodes()` is idempotent and safe to call at app/worker startup.
"""

from app.modules.nodes.base import Node, NodeSpec
from app.modules.nodes.registry import NodeRegistry, registry


def register_builtin_nodes() -> None:
    # Import for registration side effects. Keep imports local to avoid cycles.
    from app.modules.nodes.builtin import (  # noqa: F401
        ai_node,
        condition_node,
        delay_node,
        github_node,
        gmail_node,
        http_node,
        storage_node,
    )


__all__ = ["Node", "NodeSpec", "NodeRegistry", "registry", "register_builtin_nodes"]
