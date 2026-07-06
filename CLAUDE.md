# Nexus — Developer Guide for Claude Code

> Read `status.md` first. This file covers extensibility patterns.

## Adding a new node type (the most common task)

Everything lives in `backend/app/modules/nodes/builtin/`. One file = one node (or a small family sharing a connection type).

### 1. Create the node file

```python
# backend/app/modules/nodes/builtin/slack_node.py
from app.modules.nodes.base import ExecutionContext, Node, NodeSpec
from app.modules.nodes.registry import registry


class SlackSendMessageNode(Node):
    spec = NodeSpec(
        type="slack.send_message",
        title="Send Slack message",
        category="messaging",
        description="Post a message to a Slack channel via incoming webhook.",
        config_schema={
            "type": "object",
            "required": ["webhook_url", "text"],
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "title": "Webhook URL",
                    "description": "Slack incoming webhook URL",
                },
                "text": {
                    "type": "string",
                    "title": "Message",
                    "x-widget": "textarea",
                    "description": "Supports {{ nodes.<id>.output.<path> }} templates",
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

        url = config["webhook_url"]
        assert_url_is_safe(url)  # blocks SSRF
        async with httpx.AsyncClient() as client:
            r = await client.post(url, json={"text": config["text"]})
            r.raise_for_status()
        return {"ok": True}


registry.register(SlackSendMessageNode)
```

### 2. Register the import

Add one line to `backend/app/modules/nodes/builtin/__init__.py`:

```python
from . import slack_node  # noqa: F401
```

That's it. The node now:
- Appears in `GET /api/nodes` (node palette)
- Is available for AI workflow generation (system prompt auto-builds from registry)
- Gets schema-driven config forms in the builder (no frontend changes)

### Key contracts

| Thing | Where |
|-------|-------|
| `NodeSpec.config_schema` | JSON Schema — drives frontend form AND AI generation AND validation |
| `NodeSpec.output_schema` | Documents what `execute()` returns — drives template autocompletion |
| `ctx.resolve(config)` | Call this in `execute()` to expand `{{ nodes.x.output.y }}` templates |
|  `ctx.services.get_credentials` | async callable — `await ctx.services.get_credentials(connection_id)` returns the decrypted credentials dict |
| `assert_url_is_safe(url)` | SSRF guard — required for any node that makes outbound HTTP |

### Nodes that need OAuth credentials

Set `requires_connection=True` in `NodeSpec`. Users wire up the connection in Settings → Connections. In `execute()`:

```python
creds = await ctx.services.get_credentials(config["connection_id"])
token = creds["access_token"]
```

### `x-widget` overrides in config_schema

| Value | Renders as |
|-------|-----------|
| `"textarea"` | Multi-line text area |
| (default) | Single-line input |

---

## Project layout cheat-sheet

```
backend/app/
  core/           config, security (Fernet + SSRF), errors, db
  modules/
    nodes/        base.py, registry.py, builtin/
    engine/       graph.py (DAG), executor.py, resolver.py (templates)
    ai/           service.py (LiteLLM), generator.py (workflow gen)
    integrations/ oauth.py, vault.py
    auth/         dependencies.py (Firebase + dev bypass)
    runs/         store.py (PostgresRunStore)
    workflows/    service.py (CRUD)
  api/            routes: auth, workflows, runs, nodes, ai, integrations
  workers/        main.py (arq entrypoint + execute_workflow job)
```

## Running locally

```bash
# Start Postgres + Redis
docker compose up -d db redis

# Backend (dev mode)
cd backend
cp .env.example .env        # edit ENCRYPTION_KEY at minimum
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# Worker (separate terminal)
python -m app.workers.main

# Frontend
cd frontend
npm install
npm run dev
```

Auth: `AUTH_DEV_BYPASS=true` + `X-Dev-User-Id: dev-user-001` header. No Firebase needed locally.

## Running tests

```bash
cd backend
pytest tests/ -v
```

16 tests (engine + AI generator + integrations). All must pass before merging.
