"""GitHub integration nodes.

Covers the most useful automation triggers: list repos, get a PR, create an issue.
Uses the GitHub REST API v3 with a user OAuth token from the credential vault.
"""

from __future__ import annotations

from typing import Any

from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


@registry.register
class GitHubListReposNode(Node):
    spec = NodeSpec(
        type="github.list_repos",
        title="GitHub: List Repos",
        category="integration",
        description="List your GitHub repositories.",
        icon="zap",
        requires_connection="github",
        config_schema={
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "title": "Connection"},
                "visibility": {
                    "type": "string",
                    "title": "Visibility",
                    "default": "all",
                    "enum": ["all", "public", "private"],
                },
                "max_results": {"type": "integer", "title": "Max results", "default": 10, "minimum": 1, "maximum": 100},
            },
            "required": ["connection_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "repos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "full_name": {"type": "string"},
                            "description": {"type": "string"},
                            "url": {"type": "string"},
                            "stars": {"type": "integer"},
                            "language": {"type": "string"},
                        },
                    },
                }
            },
        },
    )

    async def execute(self, ctx: ExecutionContext, config: dict[str, Any]) -> dict[str, Any]:
        creds = await ctx.services.get_credentials(config["connection_id"])
        token = creds.get("access_token", "")
        resp = await ctx.services.http.get(
            "https://api.github.com/user/repos",
            headers=_gh_headers(token),
            params={"visibility": config.get("visibility", "all"), "per_page": config.get("max_results", 10)},
        )
        resp.raise_for_status()
        return {
            "repos": [
                {
                    "full_name": r["full_name"],
                    "description": r.get("description", ""),
                    "url": r["html_url"],
                    "stars": r["stargazers_count"],
                    "language": r.get("language", ""),
                }
                for r in resp.json()
            ]
        }


@registry.register
class GitHubGetPRNode(Node):
    spec = NodeSpec(
        type="github.get_pull_request",
        title="GitHub: Get Pull Request",
        category="integration",
        description="Get details and diff of a GitHub pull request.",
        icon="zap",
        requires_connection="github",
        config_schema={
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "title": "Connection"},
                "owner": {"type": "string", "title": "Owner", "description": "GitHub username or org"},
                "repo": {"type": "string", "title": "Repository name"},
                "pr_number": {"type": "integer", "title": "PR number"},
            },
            "required": ["connection_id", "owner", "repo", "pr_number"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "body": {"type": "string"},
                "state": {"type": "string"},
                "author": {"type": "string"},
                "url": {"type": "string"},
                "changed_files": {"type": "integer"},
                "additions": {"type": "integer"},
                "deletions": {"type": "integer"},
            },
        },
    )

    async def execute(self, ctx: ExecutionContext, config: dict[str, Any]) -> dict[str, Any]:
        creds = await ctx.services.get_credentials(config["connection_id"])
        token = creds.get("access_token", "")
        owner, repo, pr = config["owner"], config["repo"], int(config["pr_number"])

        resp = await ctx.services.http.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr}",
            headers=_gh_headers(token),
        )
        resp.raise_for_status()
        pr_data = resp.json()

        return {
            "title": pr_data["title"],
            "body": pr_data.get("body") or "",
            "state": pr_data["state"],
            "author": pr_data["user"]["login"],
            "url": pr_data["html_url"],
            "changed_files": pr_data.get("changed_files", 0),
            "additions": pr_data.get("additions", 0),
            "deletions": pr_data.get("deletions", 0),
        }


@registry.register
class GitHubCreateIssueNode(Node):
    spec = NodeSpec(
        type="github.create_issue",
        title="GitHub: Create Issue",
        category="integration",
        description="Create a new issue in a GitHub repository.",
        icon="zap",
        requires_connection="github",
        config_schema={
            "type": "object",
            "properties": {
                "connection_id": {"type": "string", "title": "Connection"},
                "owner": {"type": "string", "title": "Owner"},
                "repo": {"type": "string", "title": "Repository name"},
                "title": {"type": "string", "title": "Issue title", "x-widget": "textarea"},
                "body": {"type": "string", "title": "Issue body", "x-widget": "textarea"},
                "labels": {"type": "string", "title": "Labels (comma-separated)"},
            },
            "required": ["connection_id", "owner", "repo", "title"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer"},
                "url": {"type": "string"},
                "title": {"type": "string"},
            },
        },
    )

    async def execute(self, ctx: ExecutionContext, config: dict[str, Any]) -> dict[str, Any]:
        creds = await ctx.services.get_credentials(config["connection_id"])
        token = creds.get("access_token", "")
        owner, repo = config["owner"], config["repo"]
        labels = [l.strip() for l in config.get("labels", "").split(",") if l.strip()]

        resp = await ctx.services.http.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=_gh_headers(token),
            json={"title": config["title"], "body": config.get("body", ""), "labels": labels},
        )
        resp.raise_for_status()
        issue = resp.json()
        return {
            "issue_number": issue["number"],
            "url": issue["html_url"],
            "title": issue["title"],
        }


def _gh_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
