from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


class SlackSendMessageNode(Node):
    spec = NodeSpec(
        type="slack.send_message",
        title="Slack: Send Message",
        category="messaging",
        description="Post a message to a Slack channel via incoming webhook.",
        config_schema={
            "type": "object",
            "required": ["webhook_url", "text"],
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook URL",
                    "description": "Slack incoming webhook URL (api.slack.com/apps → Incoming Webhooks)",
                },
                "text": {
                    "type": "string",
                    "title": "Message",
                    "x-widget": "textarea",
                    "description": "Message text. Supports {{ nodes.<id>.output.<path> }} templates. Markdown supported.",
                },
                "username": {
                    "type": "string",
                    "title": "Bot username (optional)",
                    "description": "Override the webhook's display name.",
                },
                "icon_emoji": {
                    "type": "string",
                    "title": "Icon emoji (optional)",
                    "description": "e.g. :robot_face:",
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {"ok": {"type": "boolean"}},
        },
        icon="slack",
    )

    async def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        import httpx
        from app.core.security import assert_url_is_safe

        config = ctx.resolve(config)
        url = config["webhook_url"]
        assert_url_is_safe(url)

        payload: dict = {"text": config["text"]}
        if config.get("username"):
            payload["username"] = config["username"]
        if config.get("icon_emoji"):
            payload["icon_emoji"] = config["icon_emoji"]

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()

        return {"ok": True}


registry.register(SlackSendMessageNode)
