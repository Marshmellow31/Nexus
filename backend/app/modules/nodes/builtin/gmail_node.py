"""Gmail integration nodes.

Uses the Google Gmail REST API with the OAuth access token from the credential vault.
Two nodes: list recent messages, read a specific message (with body decoding).
"""

from __future__ import annotations

import base64
from typing import Any

from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


@registry.register
class GmailListNode(Node):
    spec = NodeSpec(
        type="gmail.list_messages",
        title="Gmail: List Messages",
        category="integration",
        description="List recent Gmail messages matching an optional query.",
        icon="zap",
        requires_connection="google",
        config_schema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "string",
                    "title": "Connection",
                    "description": "Your Google connection ID from Settings → Connections.",
                },
                "query": {
                    "type": "string",
                    "title": "Search query",
                    "description": "Gmail search query, e.g. 'is:unread from:boss@co.com'",
                    "default": "is:unread",
                },
                "max_results": {
                    "type": "integer",
                    "title": "Max results",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
            },
            "required": ["connection_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "messages": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "thread_id": {"type": "string"},
                            "snippet": {"type": "string"},
                            "subject": {"type": "string"},
                            "from": {"type": "string"},
                        },
                    },
                },
                "count": {"type": "integer"},
            },
        },
    )

    async def execute(self, ctx: ExecutionContext, config: dict[str, Any]) -> dict[str, Any]:
        creds = await ctx.services.get_credentials(config["connection_id"])
        token = creds.get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "q": config.get("query", "is:unread"),
            "maxResults": config.get("max_results", 10),
        }

        resp = await ctx.services.http.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=headers,
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()

        messages = []
        for msg_ref in data.get("messages", []):
            detail_resp = await ctx.services.http.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_ref['id']}",
                headers=headers,
                params={"format": "metadata", "metadataHeaders": ["Subject", "From"]},
            )
            if detail_resp.status_code == 200:
                msg = detail_resp.json()
                headers_list = msg.get("payload", {}).get("headers", [])
                subject = next((h["value"] for h in headers_list if h["name"] == "Subject"), "")
                from_ = next((h["value"] for h in headers_list if h["name"] == "From"), "")
                messages.append({
                    "id": msg["id"],
                    "thread_id": msg.get("threadId", ""),
                    "snippet": msg.get("snippet", ""),
                    "subject": subject,
                    "from": from_,
                })

        return {"messages": messages, "count": len(messages)}


@registry.register
class GmailReadNode(Node):
    spec = NodeSpec(
        type="gmail.read_message",
        title="Gmail: Read Message",
        category="integration",
        description="Read the full body of a Gmail message by ID.",
        icon="zap",
        requires_connection="google",
        config_schema={
            "type": "object",
            "properties": {
                "connection_id": {
                    "type": "string",
                    "title": "Connection",
                },
                "message_id": {
                    "type": "string",
                    "title": "Message ID",
                    "description": "Supports {{ nodes.<id>.output.messages.0.id }}",
                },
            },
            "required": ["connection_id", "message_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "from": {"type": "string"},
                "body": {"type": "string"},
                "date": {"type": "string"},
            },
        },
    )

    async def execute(self, ctx: ExecutionContext, config: dict[str, Any]) -> dict[str, Any]:
        creds = await ctx.services.get_credentials(config["connection_id"])
        token = creds.get("access_token", "")
        headers = {"Authorization": f"Bearer {token}"}

        resp = await ctx.services.http.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{config['message_id']}",
            headers=headers,
            params={"format": "full"},
        )
        resp.raise_for_status()
        msg = resp.json()

        payload = msg.get("payload", {})
        hdr = {h["name"]: h["value"] for h in payload.get("headers", [])}
        body = _extract_body(payload)

        return {
            "subject": hdr.get("Subject", ""),
            "from": hdr.get("From", ""),
            "date": hdr.get("Date", ""),
            "body": body,
        }


def _extract_body(payload: dict[str, Any]) -> str:
    """Recursively extract plain-text body from Gmail message payload."""
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        text = _extract_body(part)
        if text:
            return text
    return ""
