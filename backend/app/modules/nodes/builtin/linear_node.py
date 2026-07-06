from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


class LinearCreateIssueNode(Node):
    spec = NodeSpec(
        type="linear.create_issue",
        title="Linear: Create Issue",
        category="integration",
        description="Create a new issue in a Linear team.",
        requires_connection="linear",
        config_schema={
            "type": "object",
            "required": ["connection_id", "team_id", "title"],
            "properties": {
                "connection_id": {
                    "type": "string",
                    "title": "Linear Connection",
                    "description": "Select your Linear connection from Settings → Connections",
                },
                "team_id": {
                    "type": "string",
                    "title": "Team ID",
                    "description": "Linear team ID (found in team settings URL)",
                },
                "title": {
                    "type": "string",
                    "title": "Issue title",
                    "description": "Supports {{ nodes.<id>.output.<path> }} templates.",
                },
                "description": {
                    "type": "string",
                    "title": "Description (optional)",
                    "x-widget": "textarea",
                    "description": "Markdown supported.",
                },
                "priority": {
                    "type": "number",
                    "title": "Priority (0=none, 1=urgent, 2=high, 3=medium, 4=low)",
                    "default": 0,
                    "enum": [0, 1, 2, 3, 4],
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "issue_id": {"type": "string"},
                "identifier": {"type": "string"},
                "url": {"type": "string"},
            },
        },
        icon="zap",
    )

    async def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        import httpx

        config = ctx.resolve(config)
        creds = await ctx.services.vault.get_credentials(config["connection_id"])
        token = creds["api_key"]

        mutation = """
        mutation CreateIssue($teamId: String!, $title: String!, $description: String, $priority: Int) {
          issueCreate(input: {
            teamId: $teamId
            title: $title
            description: $description
            priority: $priority
          }) {
            success
            issue {
              id
              identifier
              url
            }
          }
        }
        """
        variables = {
            "teamId": config["team_id"],
            "title": config["title"],
            "description": config.get("description"),
            "priority": int(config.get("priority", 0)),
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.linear.app/graphql",
                headers={
                    "Authorization": token,
                    "Content-Type": "application/json",
                },
                json={"query": mutation, "variables": variables},
            )
            r.raise_for_status()
            data = r.json()

        issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
        return {
            "issue_id": issue.get("id", ""),
            "identifier": issue.get("identifier", ""),
            "url": issue.get("url", ""),
        }


class LinearListIssuesNode(Node):
    spec = NodeSpec(
        type="linear.list_issues",
        title="Linear: List Issues",
        category="integration",
        description="List recent issues from your Linear team.",
        requires_connection="linear",
        config_schema={
            "type": "object",
            "required": ["connection_id", "team_id"],
            "properties": {
                "connection_id": {
                    "type": "string",
                    "title": "Linear Connection",
                },
                "team_id": {
                    "type": "string",
                    "title": "Team ID",
                },
                "max_results": {
                    "type": "number",
                    "title": "Max results",
                    "default": 20,
                },
            },
        },
        output_schema={
            "type": "object",
            "properties": {
                "issues": {"type": "array"},
                "count": {"type": "number"},
            },
        },
        icon="list",
    )

    async def execute(self, ctx: ExecutionContext, config: dict) -> dict:
        import httpx

        config = ctx.resolve(config)
        creds = await ctx.services.vault.get_credentials(config["connection_id"])
        token = creds["api_key"]

        limit = int(config.get("max_results", 20))
        query = """
        query TeamIssues($teamId: String!, $first: Int!) {
          team(id: $teamId) {
            issues(first: $first, orderBy: updatedAt) {
              nodes {
                id
                identifier
                title
                state { name }
                priority
                url
              }
            }
          }
        }
        """

        async with httpx.AsyncClient() as client:
            r = await client.post(
                "https://api.linear.app/graphql",
                headers={
                    "Authorization": token,
                    "Content-Type": "application/json",
                },
                json={"query": query, "variables": {"teamId": config["team_id"], "first": limit}},
            )
            r.raise_for_status()
            data = r.json()

        nodes = data.get("data", {}).get("team", {}).get("issues", {}).get("nodes", [])
        issues = [
            {
                "id": i["id"],
                "identifier": i["identifier"],
                "title": i["title"],
                "state": i.get("state", {}).get("name", ""),
                "priority": i.get("priority", 0),
                "url": i.get("url", ""),
            }
            for i in nodes
        ]
        return {"issues": issues, "count": len(issues)}


registry.register(LinearCreateIssueNode)
registry.register(LinearListIssuesNode)
