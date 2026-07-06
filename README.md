# Nexus

**The AI Operating System for Everyday Automation.**

Describe an automation in plain English → Nexus generates a validated workflow you
review on a visual canvas → it runs deterministically in a background engine.

> This is not a Zapier clone with a nicer theme. The differentiator is **AI-first
> authoring**: natural language becomes a verified, deterministic DAG.

---

## Architecture

```mermaid
graph TB
    subgraph Frontend ["Frontend (React + Vite)"]
        UI[Visual Builder\nReact Flow canvas]
        CP[Command Palette\n⌘K · AI generation]
        SSE[SSE run overlay\nlive node status]
    end

    subgraph API ["API Process (FastAPI)"]
        R[REST routes\n/workflows · /runs · /nodes]
        AUTH[Firebase Auth\nor dev bypass]
        Q[Enqueue job\narq → Redis]
    end

    subgraph Worker ["Worker Process (arq)"]
        EX[Executor\ntopo sort + retry]
        NR[Node Registry\n10 built-in types]
        TR[Template Resolver\n{{ nodes.x.output.y }}]
        VS[Vault\nFernet-encrypted]
    end

    subgraph Store ["Data (Postgres)"]
        RUN[runs + run_steps\nper-node checkpoint]
        WF[workflows]
        CONN[connections\nencrypted tokens]
    end

    UI -->|PATCH definition| R
    CP -->|POST /ai/generate| R
    R -->|trigger| Q
    Q -->|execute_workflow job| EX
    EX --> NR
    EX --> TR
    EX --> VS
    EX -->|checkpoint| RUN
    SSE -->|GET /runs/:id/stream| R
    R -.->|poll| RUN
    VS --> CONN
```

Two processes, one codebase/image:
- **`api`** (FastAPI) — REST + SSE. Never executes workflows; it enqueues them.
- **`worker`** (arq) — runs the execution engine; checkpoints every node to Postgres.

**Postgres** (source of truth) · **Redis** (queue) · **Firebase** (auth) · **LiteLLM** (AI abstraction).

Real abstraction seams in exactly three places: **AI providers, node types, integration connectors**.
Everywhere else: plain services. Full design record: [status.md](status.md).

---

## The engine (the heart)

- Workflows are DAGs (`nodes` + `edges` JSON). Topo-sort → sequential execution today; parallel later with no model change.
- Nodes self-register into a registry. A node's `NodeSpec` (JSON Schema) drives frontend forms, server validation, **and** AI generation — one definition, no drift. Adding a capability = one Python file.
- Data flows via `{{ nodes.<id>.output.<path> }}` templates, resolved by a data-only lookup (no eval/Jinja — a security boundary).
- Per-node retries + timeouts + Postgres checkpointing → accurate, resumable history.

### Built-in nodes

| Node | Type |
|------|------|
| AI Generate | `ai.generate` |
| HTTP Request | `http.request` |
| Condition | `logic.condition` |
| Delay | `logic.delay` |
| Store | `action.store` |
| Gmail: List Messages | `gmail.list_messages` |
| Gmail: Read Message | `gmail.read_message` |
| GitHub: List Repos | `github.list_repos` |
| GitHub: Get Pull Request | `github.get_pull_request` |
| GitHub: Create Issue | `github.create_issue` |

---

## Security (day one)

- **Credential vault**: OAuth tokens encrypted at rest with Fernet/AES. Never appear in workflow JSON, logs, or API responses.
- **SSRF guard**: HTTP node resolves DNS and blocks private/loopback/metadata IPs before every request.
- **Webhook signatures**: HMAC-SHA256 (GitHub-style `sha256=...` header).
- **Template resolution**: data-only path lookup — no eval, no Jinja.
- **OAuth CSRF**: state parameter with 10-min TTL, Fernet-bound.

---

## Local development

```bash
# Full stack (Postgres + Redis + API + worker)
docker compose up --build

# Or run pieces individually:
cd backend
cp .env.example .env   # set ENCRYPTION_KEY (see comment in file)
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload    # API on :8000
python -m app.workers.main       # worker

cd frontend
npm install
npm run dev                      # UI on :5173
```

Auth in local dev: `AUTH_DEV_BYPASS=true` (default in `.env.example`). Hit any endpoint with `X-Dev-User-Id: dev-user-001` — no Firebase credentials needed.

```bash
# Run all tests
cd backend && pytest tests/ -v   # 16 tests
```

---

## Deploy

- **Frontend → Vercel**: import the `frontend/` directory. SPA routing is configured in [`frontend/vercel.json`](frontend/vercel.json). Point `VITE_API_URL` at your Railway API URL.
- **Backend → Railway**: uses [`railway.toml`](railway.toml). Creates two services (`api` + `worker`) from the same Docker image. Add env vars from `.env.example` in Railway dashboard.
- **Database → Neon** (Postgres) · **Queue → Upstash** (Redis): paste connection strings into Railway env vars.

---

## Extending Nexus

See [CLAUDE.md](CLAUDE.md) for the full guide on adding a new node type — it's the primary extensibility mechanism and takes ~10 lines of Python.

## Status

Phase 6 complete. See [status.md](status.md) for full progress log and architectural decisions.
