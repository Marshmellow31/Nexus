# Nexus — Project Status & Master Plan

> **Single source of truth.** Any model/dev picking up this project should read this file first.
> Update this file whenever scope, decisions, or progress change.

---

## 1. What Nexus Is

**Tagline:** The AI Operating System for Everyday Automation.

Nexus lets users automate daily tasks with AI + visual workflows. Think n8n/Zapier's engine,
Linear/Raycast/Notion's polish — but **AI-first**.

### Core identity (the differentiator — DO NOT lose this)
The hero flow is **describe → generate → review → run**:
1. User types a plain-English goal ("when my professor emails me, summarize it and add a calendar event if it has a date").
2. AI generates a **validated workflow DAG** against the node registry.
3. User reviews/edits it visually on a canvas.
4. It runs **deterministically** in a background engine.

The visual builder is the *trust & inspection* layer, not the primary authoring surface.
AI-as-authoring is what makes this NOT "just another Zapier clone."

---

## 2. Architecture Decisions (locked)

- **Modular monolith**, not textbook Clean Architecture. Real abstraction layers ONLY where
  substitution is likely: **AI providers, node types, integration connectors**. Elsewhere: plain
  services calling SQLAlchemy directly.
- **Two processes, one codebase, one Docker image:** `api` (FastAPI) and `worker` (arq).
  **Execution NEVER runs in an API request handler** — always a background job.
- **DAG model from day one; sequential (topo-sort) execution from day one.** Parallel = later,
  no data-model change.
- **Checkpoint run state to Postgres after every node** → resumable + accurate history.
- **SSE** for run status streaming (not WebSockets).
- Frontend server-state = TanStack Query ONLY. Zustand = client/UI state only (never mirror API data).

### Stack
- Frontend: React + TypeScript + Vite (SPA, not Next), Tailwind, shadcn/ui, React Flow, Framer Motion (sparingly), TanStack Query, Zustand, React Hook Form, cmdk (command palette).
- Backend: FastAPI, Python 3.12, SQLAlchemy 2.0 (async), Pydantic v2, PostgreSQL, Redis, **arq** (queue).
- Auth: Firebase Auth (Google/GitHub/email). Backend verifies Firebase ID token (JWKS cached). All Firebase contact isolated in `modules/auth/`.
- AI: **LiteLLM** normalization wrapped in our own `AIService` (metering, routing, structured output). Users bring own keys in MVP (encrypted).
- Deploy: Vercel (frontend), Railway (api+worker), Neon (Postgres), Upstash (Redis).

---

## 3. Node/Engine Contract

- `NodeSpec`: static metadata — `type`, `inputs` (JSON Schema), `outputs` (JSON Schema), `requires_connection`.
  Drives BOTH frontend forms AND validation AND AI generation.
- `Node.execute(ctx, config) -> dict`. Nodes self-register into a registry at import time.
- Frontend fetches `/api/nodes` and renders config forms generically from JSON Schema. Adding a node = one Python file.
- Data passing between nodes: template expressions `{{ nodes.<id>.output.<path> }}`, resolved by engine
  before each node. **Data-only path lookup — never eval/Jinja.**
- Each run = `runs` row; each node exec = `run_steps` row (input snapshot, output, status, timing, error).
- Retries: per-node policy (max attempts, exponential backoff). Timeouts: per-node `asyncio.wait_for` + whole-run ceiling.

---

## 4. Security Non-Negotiables

1. **Credential vault:** OAuth tokens + user API keys encrypted at rest (Fernet/AES, key from env). In `connections` table. Never in workflow JSON, logs, or API responses. Nodes reference `connection_id`; engine resolves server-side.
2. **Webhook URLs** carry unguessable secret; optional HMAC verification.
3. **SSRF guard on HTTP node:** resolve DNS, block private/link-local/metadata IPs.
4. **Rate limiting:** API requests + executions-per-user-per-hour.
5. Template resolution is data-only path lookup, no eval.
6. Every table has `user_id` now; `workspace_id` later (don't preclude multi-tenancy).

---

## 5. MVP Scope

**IN:** Auth, Dashboard, Workflow Builder, Execution Engine, nodes (AI, HTTP, Webhook, Condition, Delay[short]),
Gmail integration, GitHub integration, Webhook triggers, Execution History + run inspector, Settings, Profile, Dark mode,
**AI workflow generation (hero feature)**, command palette.

**CUT from MVP (deferred):** Google Calendar (Gmail proves the OAuth path), durable long delays (>5min),
roles/permissions system (single-user; `role` column stub only), Notes-as-a-feature (use a storage node → own DB table),
scheduling/cron (keep `trigger_type` column so it slots in later), parallel execution, teams/workspaces.

**Delay node MVP:** ≤5 min = in-worker async sleep. Longer = persisted `resume_at` + future beat process.

---

## 6. Build Order

1. **Foundation:** repo structure, backend skeleton (FastAPI app, config, db, health), frontend skeleton (Vite+Tailwind+shadcn), Docker, CI, deploy hello-world of every piece. Design tokens.
2. **Engine core:** node registry + HTTP/AI/Condition nodes, `runs`/`run_steps` model, executor (topo sort + template resolution + checkpointing), arq worker, SSE status. Drive via JSON API (no UI builder yet).
3. **Builder UI:** React Flow canvas + schema-driven config forms + run inspector.
4. **Integrations:** OAuth plumbing + credential vault + Gmail + GitHub connectors + webhook triggers.
5. **Identity feature:** AI workflow generation, command palette, polish, README + architecture docs w/ diagrams.

---

## 7. Repo Layout

```
Nexus/
  backend/
    app/
      core/          # config, security, db session, errors, logging
      modules/
        auth/        # firebase verify, user provisioning
        workflows/   # CRUD, versioning, validation
        engine/      # executor, run state, template resolver
        nodes/       # node base + implementations + registry
        integrations/# oauth mgmt, credential vault
        ai/          # provider abstraction (LiteLLM wrapper)
        runs/        # execution history
      workers/       # arq entrypoint
      main.py        # FastAPI app factory
    tests/
    pyproject.toml
    Dockerfile
  frontend/
    src/
      app/           # routing, providers
      features/      # workflows, runs, builder, auth, settings
      components/ui/ # shadcn
      lib/           # api client, query hooks, utils
    package.json
    vite.config.ts
  docker-compose.yml # local: postgres + redis + api + worker
  status.md
  README.md
```

---

## 8. Progress Log

| Date       | Milestone | Status |
|------------|-----------|--------|
| 2026-07-07 | status.md created, plan locked | ✅ |
| 2026-07-07 | Backend foundation: config, db, errors, security (Fernet+SSRF) | ✅ |
| 2026-07-07 | Engine core: registry, resolver, graph (topo/DAG), executor (retry/timeout/branch/checkpoint) | ✅ |
| 2026-07-07 | 5 built-in nodes: ai.generate, http.request, logic.condition, logic.delay, action.store | ✅ |
| 2026-07-07 | AI service (LiteLLM wrapper), FastAPI app factory, /api/health, /api/nodes | ✅ |
| 2026-07-07 | Engine tests (templates, branch pruning, cycle reject) — 3 passing | ✅ |
| 2026-07-07 | Infra: Dockerfile (one image/two entrypoints), docker-compose, arq worker, README, .env.example | ✅ |
| 2026-07-07 | Phase 2: All SQLAlchemy models (users, workflows, runs, run_steps, connections, stored_items) | ✅ |
| 2026-07-07 | Phase 2: Alembic env + migration 0001_initial_schema (all 6 tables) | ✅ |
| 2026-07-07 | Phase 2: PostgresRunStore, CredentialVault, WorkflowService, RunService | ✅ |
| 2026-07-07 | Phase 2: Firebase auth + dev bypass dependency | ✅ |
| 2026-07-07 | Phase 2: API routes — /auth/me, /workflows CRUD, /runs trigger+history+SSE stream | ✅ |
| 2026-07-07 | Phase 2: Worker fully wired to executor + real RunStore + vault | ✅ |

### What works right now
- `pytest` green (3/3): engine executes multi-node graphs, templates, branch pruning, cycle rejection.
- All 6 DB models + Alembic migration ready to run against Postgres.
- Full API: `GET /api/health`, `GET /api/nodes`, `GET /api/auth/me`, workflows CRUD, run trigger, run history, SSE stream.
- Worker is fully wired: loads run from DB → builds graph → executes with real Executor + PostgresRunStore + CredentialVault → commits.
- Dev bypass: hit any route with `X-Dev-User-Id: any-string` header, no Firebase needed locally.

### Phase 3 complete ✅

| 2026-07-07 | Phase 4: AI workflow generator — system-prompt from live registry, DAG validation, retry | ✅ |
| 2026-07-07 | Phase 4: POST /api/ai/generate-workflow endpoint | ✅ |
| 2026-07-07 | Phase 4: React Flow builder canvas — NexusNode, NodePalette, ConfigPanel (schema-driven) | ✅ |
| 2026-07-07 | Phase 4: Live SSE run-status overlay on canvas nodes | ✅ |
| 2026-07-07 | Phase 4: Command palette AI generation mode (describe → generate → navigate to canvas) | ✅ |
| 2026-07-07 | Phase 4: Code-split builder chunk — initial bundle 372KB, builder 186KB | ✅ |
| 2026-07-07 | Phase 4: Frontend build clean, backend tests 3/3, AI catalogue 3413 chars | ✅ |

### What works end-to-end right now
1. Hit `/workflows/new` → visual canvas with node palette
2. Click any node in palette → it appears on canvas
3. Click node → config panel auto-renders from JSON Schema (no hardcoding)
4. Draw edges to connect nodes
5. Click Run → triggers a real run via API → SSE stream → node status overlays update live
6. Press ⌘K → "Generate workflow with AI" → describe in plain English → canvas populates
7. All changes auto-save (1.5s debounce) with PATCH to API

| 2026-07-07 | Phase 5: OAuth manager (Google, GitHub) — auth URL, CSRF state, code exchange | ✅ |
| 2026-07-07 | Phase 5: /api/integrations routes — connect, callback, list, delete, webhook trigger | ✅ |
| 2026-07-07 | Phase 5: Gmail nodes (list_messages, read_message) — full Gmail REST API integration | ✅ |
| 2026-07-07 | Phase 5: GitHub nodes (list_repos, get_pull_request, create_issue) | ✅ |
| 2026-07-07 | Phase 5: Webhook trigger endpoint with HMAC verification | ✅ |
| 2026-07-07 | Phase 5: Dark mode toggle (light/dark/system, persists to localStorage) | ✅ |
| 2026-07-07 | Phase 5: Framer Motion route transitions (AnimatePresence, 180ms ease) | ✅ |
| 2026-07-07 | Phase 5: Settings page — profile + connections management (connect/disconnect) | ✅ |
| 2026-07-07 | Phase 5: AI generator now validates node types against registry (bug fix) | ✅ |
| 2026-07-07 | Phase 5: 8 tests passing (3 engine + 5 AI generator) | ✅ |
| 2026-07-07 | Phase 5: Bundle split — initial 61KB, vendor 247KB, motion 125KB, builder 160KB | ✅ |

### What the full system does end-to-end
- 10 node types: ai.generate, http.request, logic.condition, logic.delay, action.store, gmail.list_messages, gmail.read_message, github.list_repos, github.get_pull_request, github.create_issue
- Full OAuth flow for Google and GitHub (redirect → consent → token exchange → encrypted storage)
- Webhook triggers with HMAC signature verification
- Complete visual builder + schema-driven config + live SSE run status overlays
- AI workflow generation from plain English (⌘K → describe → canvas populates)
- Dark/light/system theme, Framer Motion page transitions
- 11 API routes, 8 tests passing, no TypeScript errors, clean production build

### Phase 6 complete ✅

| 2026-07-07 | Phase 6: tests/test_integrations.py — webhook HMAC (5 cases) + vault round-trip | ✅ |
| 2026-07-07 | Phase 6: 16 tests total, all passing | ✅ |
| 2026-07-07 | Phase 6: .github/workflows/ci.yml — ruff + pyright + pytest + tsc + vite build | ✅ |
| 2026-07-07 | Phase 6: frontend/vercel.json — SPA rewrite + immutable asset cache headers | ✅ |
| 2026-07-07 | Phase 6: railway.toml — api + worker services from one Docker image | ✅ |
| 2026-07-07 | Phase 6: CLAUDE.md — step-by-step guide for adding a new node type | ✅ |
| 2026-07-07 | Phase 6: README.md — Mermaid architecture diagram + deploy guide + node table | ✅ |

### Next steps (Phase 7 → Production hardening, if needed)
- Wire `alembic upgrade head` into Dockerfile CMD or Railway predeploy hook
- Real Firebase token verification (replace dev bypass for production env)
- Rate limiting middleware (slowapi — already in pyproject.toml, not yet wired)
- Scheduling/cron support (trigger_type="schedule" column exists; beat process needed)
- More integrations: Discord webhook, Slack, Notion
- Parallel node execution in Executor (data model already supports it)

### Notes / gotchas for future sessions
- Local Python is 3.13 (pyproject targets 3.12 for Docker — fine).
- `core/errors.py` keeps FastAPI import lazy so the engine stays importable without web deps (domain/framework separation).
- Users bring own AI keys in MVP; metering hook lives in `AIService.generate` (TODO).
