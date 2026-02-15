# infrastructure/ — Concrete Implementations

## Rules
- This layer implements protocols defined in `core/protocols/`.
- MAY import from `core/`. NEVER import from `api/` or `cli/`.
- New implementations must satisfy the corresponding protocol interface.

## Structure
- `database/` — SQLAlchemy async engine, session factory, generic repository.
- `ebay_mock/` — `MockEbayClient` implementing `EbayGateway`. Stateful in-memory mock with fixture data.
- `ebay/` — `RealEbayClient` implementing `EbayGateway`. OAuth 2.0 token manager, rate limiter, 7 endpoint modules.
- `scheduler/` — APScheduler integration. Job registry defines schedules, `apscheduler_impl.py` wraps the scheduler.

## Conventions
- Mock client is for tests and local dev. Real client is for sandbox/production.
- Database sessions are scoped per-request (API) or per-job (scheduler).
- Rate limiter uses exponential backoff. Do not bypass it.
- Scheduler jobs must be idempotent — they can fire more than once safely.
