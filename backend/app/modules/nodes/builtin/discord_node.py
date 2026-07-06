from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


class DiscordSendMessageNode(Node):
    spec = NodeSpec(
        type="discord.send_message",
        title="Discord: Send Message",
        category="messaging",
        description="Post a message to a Discord channel via incoming webhook.",
        config_schema={
            "type": "object",
            "required": ["webhook_url", "content"],
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook URL",
                    "description": "Discord channel webhook URL (Server Settings → Integrations → Webhooks)",
                },
                "content": {
                    "type": "string",
                    "title": "Message",
                    "x-widget": "textarea",
                    "description": "Message text. Supports {{ nodes.<id>.output.<path> }} templates.",
                },
                "username": {
                    "type": "string",
                    "title": "Bot username (optional)",
                    "description": "Override the webhook's display name.",
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
        },
        icon="message-circle",
    )

    async def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        import httpx
        from app.core.security import assert_url_is_safe

        config = ctx.resolve(config)
        url = config["webhook_url"]
        assert_url_is_safe(url)

        payload: dict = {"content": config["content"]}
        if config.get("username"):
            payload["username"] = config["username"]

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()

        return {"ok": True}


registry.register(DiscordSendMessageNode)
