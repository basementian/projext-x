# FlipFlow — Build Batches

Each batch is scoped to fit in a single Claude Code session while maintaining test coverage and quality.

---

## Batch 1: Scheduler Wiring
**Goal:** Make the automation engine actually run.

**Scope:**
- Replace 9 placeholder jobs in `job_registry.py` with real service calls
- Wire scheduler into FastAPI app lifespan (start on boot, graceful shutdown)
- Record every job execution to `JobLog` model
- Dependency injection: each job gets its own DB session + eBay client

**Files touched:**
- `infrastructure/scheduler/job_registry.py` — real job functions
- `infrastructure/scheduler/apscheduler_impl.py` — minor tweaks if needed
- `api/app.py` — lifespan hook for scheduler start/stop
- New: `infrastructure/scheduler/job_runner.py` — orchestrator that wires services to sessions

**Tests:** Unit test each job function, integration test scheduler start/stop
**Estimate:** ~350 lines new code + ~200 lines tests

---

## Batch 2: CLI Completion
**Goal:** Fill the two empty CLI command groups.

**Scope:**
- `scheduler` commands: `status`, `list-jobs`, `pause <job>`, `resume <job>`, `trigger <job>`
- `db` commands: `init`, `migrate`, `seed` (wraps Alembic + fixture loading)

**Files touched:**
- New: `cli/commands/scheduler.py`
- New: `cli/commands/db.py`
- `cli/main.py` — register new groups

**Tests:** CLI runner tests for each command
**Estimate:** ~200 lines new code + ~100 lines tests

---

## Batch 3: Dashboard + Zombie UI Wiring
**Goal:** Make the two most important screens live.

**Scope:**
- `dashboard.html` — fetch health, listing stats, zombie count, queue status, recent offers
- `zombie-killer.html` — fetch zombie scan results, trigger resurrect, show status updates
- Add aggregate endpoint `GET /api/v1/stats/dashboard` (returns combined metrics in one call)

**Files touched:**
- `ui/dashboard.html` — add fetch calls, populate DOM
- `ui/zombie-killer.html` — add fetch calls, wire action buttons
- New: `api/routers/stats.py` — dashboard aggregate endpoint
- `api/app.py` — register stats router

**Tests:** API test for stats endpoint
**Estimate:** ~250 lines JS + ~80 lines Python + ~50 lines tests

---

## Batch 4: Remaining UI Screens
**Goal:** Wire the last 3 screens to the API.

**Scope:**
- `scanner-results.html` — fetch listings, display STR analysis
- `onboarding.html` — eBay connection status check, may need `GET /api/v1/ebay/status` endpoint
- `ab-test.html` — placeholder wiring (A/B infrastructure is Tier 2, wire what exists)

**Files touched:**
- `ui/scanner-results.html`, `ui/onboarding.html`, `ui/ab-test.html`
- New: `api/routers/ebay_status.py` (if needed)

**Tests:** API test for any new endpoints
**Estimate:** ~300 lines JS + ~60 lines Python

---

## Batch 5: Analytics Service
**Goal:** Turn the `ListingSnapshot` model into actionable data.

**Scope:**
- New service: `SnapshotCollector` — daily snapshot of all active listings (views, watchers, price, status)
- New scheduler job: snapshot collection (daily)
- API endpoints: `GET /api/v1/analytics/trends` (listing performance over time), `GET /api/v1/analytics/summary` (portfolio-level metrics)
- Wire into dashboard if Batch 3 is done

**Files touched:**
- New: `core/services/snapshot_collector.py`
- `infrastructure/scheduler/job_registry.py` — add snapshot job
- New: `api/routers/analytics.py`

**Tests:** Unit tests for collector logic, API tests for endpoints
**Estimate:** ~250 lines new code + ~150 lines tests

---

## Batch 6: API Hardening
**Goal:** Production-grade request handling.

**Scope:**
- Per-endpoint rate limiting (slowapi or custom middleware)
- Standardized error responses (consistent JSON error format)
- Request validation tightening (stricter Pydantic schemas where loose)
- Add `X-Request-ID` header for tracing

**Files touched:**
- `api/app.py` — rate limit middleware
- `api/routers/*` — error response consistency pass
- `core/schemas/` — tighten validation

**Tests:** Rate limit tests, error format tests
**Estimate:** ~200 lines new code + ~100 lines tests

---

## Batch 7: Deploy Prep
**Goal:** Ready for real deployment.

**Scope:**
- PostgreSQL config + connection pooling
- Docker Compose (API + DB + scheduler)
- Environment config validation (pydantic-settings)
- Alembic migration verification against Postgres
- Final integration test pass

**Files touched:**
- `infrastructure/database/` — Postgres engine config
- New: `Dockerfile`, `docker-compose.yml`
- `core/config.py` — env validation
- `alembic/` — verify migration

**Tests:** Integration tests against Postgres
**Estimate:** ~300 lines config + ~100 lines tests

---

## Batch Order

```
Batch 1 (Scheduler)  ──→  Batch 2 (CLI)
       ↓
Batch 3 (Dashboard UI)  ──→  Batch 4 (Remaining UI)
       ↓
Batch 5 (Analytics)
       ↓
Batch 6 (API Hardening)  ──→  Batch 7 (Deploy)
```

Batches 1 and 3 can run in parallel. Batch 2 depends on Batch 1. Batch 4 depends on Batch 3. Everything else is sequential.

## Quality Gates (every batch)
- All existing tests still pass (355+)
- New code has test coverage
- `ruff` lint clean
- PROGRESS.md updated
