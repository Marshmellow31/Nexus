from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


class NotionSearchNode(Node):
    spec = NodeSpec(
        type="notion.search",
        title="Notion: Search",
        category="integration",
        description="Search pages and databases in your Notion workspace.",
        requires_connection="notion",
        config_schema={
            "type": "object",
            "required": [],
            "properties": {
                "connection_id": {
                    "type": "string",
                    "title": "Notion Connection",
                    "description": "Select your Notion connection from Settings → Connections",
                },
                "query": {
                    "type": "string",
                    "title": "Search query",
                    "description": "Text to search for. Leave blank to list all accessible pages.",
                },
                "max_results": {
                    "type": "number",
                    "title": "Max results",
                    "default": 10,
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "count": {"type": "number"},
            },
        },
        icon="file-text",
    )

    async def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        import httpx

        config = ctx.resolve(config)
        creds = await ctx.services.vault.get_credentials(config["connection_id"])
        token = creds["api_key"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        body: dict = {"page_size": int(config.get("max_results", 10))}
        if config.get("query"):
            body["query"] = config["query"]

        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.notion.com/v1/search",
                headers=headers,
                json=body,
            )
            r.raise_for_status()
            data = r.json()

        results = data.get("results", [])
        simplified = [
            {
                "id": p.get("id"),
                "title": _extract_title(p),
                "url": p.get("url"),
                "type": p.get("object"),
            }
            for p in results
        ]
        return {"results": simplified, "count": len(simplified)}


class NotionCreatePageNode(Node):
    spec = NodeSpec(
        type="notion.create_page",
        title="Notion: Create Page",
        category="integration",
        description="Create a new page inside a Notion database or parent page.",
        requires_connection="notion",
        config_schema={
            "type": "object",
            "required": ["connection_id", "parent_id", "title"],
            "properties": {
                "connection_id": {
                    "type": "string",
                    "title": "Notion Connection",
                },
                "parent_id": {
                    "type": "string",
                    "title": "Parent page or database ID",
                    "description": "The ID from the Notion URL (32-char string after the last dash).",
                },
                "title": {
                    "type": "string",
                    "title": "Page title",
                    "description": "Supports {{ nodes.<id>.output.<path> }} templates.",
                },
                "content": {
                    "type": "string",
                    "title": "Body text (optional)",
                    "x-widget": "textarea",
                    "description": "Plain text content for the page body.",
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "page_id": {"type": "string"},
                "url": {"type": "string"},
            },
        },
        icon="file-plus",
    )

    async def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        import httpx

        config = ctx.resolve(config)
        creds = await ctx.services.vault.get_credentials(config["connection_id"])
        token = creds["api_key"]

        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }

        parent_id = config["parent_id"].replace("-", "")
        children = []
        if config.get("content"):
            children = [{
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": config["content"]}}]
                },
            }]

        body = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": {
                    "title": [{"type": "text", "text": {"content": config["title"]}}]
                }
            },
            "children": children,
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=body,
            )
            r.raise_for_status()
            data = r.json()

        return {"page_id": data.get("id", ""), "url": data.get("url", "")}


def _extract_title(page: dict) -> str:
    props = page.get("properties", {})
    for val in props.values():
        if val.get("type") == "title":
            parts = val.get("title", [])
            return "".join(p.get("plain_text", "") for p in parts)
    return page.get("id", "")


registry.register(NotionSearchNode)
registry.register(NotionCreatePageNode)
