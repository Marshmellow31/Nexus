"""HTTP request node. SSRF-guarded: users can point this at any URL, so we resolve
and reject non-public addresses before making the request."""

from __future__ import annotations

from typing import Any

from app.core.security import assert_url_is_safe
from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


@registry.register
class HttpRequestNode(Node):
    spec = NodeSpec(
        type="http.request",
        title="HTTP Request",
        category="action",
        description="Call any REST API. Blocks requests to internal/private addresses.",
        icon="globe",
        config_schema={
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "title": "Method",
                    "default": "GET",
                    "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"],
                },
                "url": {"type": "string", "title": "URL"},
                "headers": {"type": "object", "title": "Headers"},
                "body": {"type": "object", "title": "JSON body"},
            },
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "body": {},
                "headers": {"type": "object"},
            },
        },
    )

    async def execute(
        self, ctx: ExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        url = config["url"]
        assert_url_is_safe(url)
        resp = await ctx.services.http.request(
            config.get("method", "GET"),
            url,
            headers=config.get("headers") or None,
            json=config.get("body") or None,
        )
        try:
            body: Any = resp.json()
        except Exception:  # noqa: BLE001 - non-JSON response
            body = resp.text
        return {"status": resp.status_code, "body": body, "headers": dict(resp.headers)}
