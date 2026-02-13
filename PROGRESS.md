# FlipFlow — Progress

## Current Status
**Phase:** Production Readiness
**Tests:** 355 passing
**Stack:** Python 3.12 / FastAPI / SQLAlchemy async / Typer CLI

## What's Working
- **Profit Floor Calculator** — full fee breakdown (eBay 13% + payment 2.9% + ads), min viable price calc
- **Title Sanitizer** — junk strip, spam removal, ALL CAPS normalization, brand/model front-loading
- **Mobile Enforcer** — HTML stripping (scripts, styles, comments), responsive template wrapping, mobile safety check
- **STR Enforcer** — manual sell-through rate validation (40% threshold), override support, STR calculation
- **Zombie Killer** — scans active listings >60 days with <10 views, flags zombies, escalates to purgatory after 3 cycles
- **Resurrector** — end listing → cooldown → rotate photos → create fresh Item ID
- **SmartQueue** — priority-based queue, Sunday 8-10 PM ET surge window, batch release
- **Store Pulse** — monthly handling time toggle (1→2 days) to force eBay re-indexing
- **Photo Shuffler** — rotates main photo on 0-view listings past 14 days threshold
- **Kickstarter** — auto-promotes new listings at 1.5% CPS for 14 days, campaign cleanup
- **Purgatory** — break-even pricing, 30% markdown, donate/trash suggestion after 7 days
- **Offer Sniper V2** — tiered age-based offers, per-watcher cooldown, inbound offer handling (accept/counter/reject)
- **Graduated Repricer** — time-based markdown ladder (7d:5%, 14d:10%, 30d:15%, 45d:20%), profit floor enforced
- **Auto Relister** — preventive relisting every 30 days for low-traffic items
- **REST API** — health, listings CRUD, zombie scan/resurrect, queue, repricer, relister, offers
- **Mock eBay Client** — stateful in-memory mock implementing EbayGateway protocol
- **Real eBay Client** — OAuth 2.0 token manager, rate limiter with backoff, 7 endpoint modules
- **Scheduler** — APScheduler with job registry (zombie scan, queue release, store pulse, etc.)
- **Android App** — Expo/React Native, 5-tab layout, API integration
- **Web UI** — 5 Tailwind prototype screens served from FastAPI (dashboard, onboarding, scanner, zombie killer, A/B test)

## Production Readiness (2026-02-13)
- **API Key Authentication** — X-API-Key middleware on all endpoints (health is public), configurable via env
- **CORS Lockdown** — configurable allowed origins (no more wildcard `*`)
- **Structured Logging** — Python logging across all 10 services with error context and operation summaries
- **GitHub Actions CI/CD** — automated pytest, ruff lint, mypy on push/PR
- **Alembic Initial Migration** — full schema (9 tables) with upgrade/downgrade
- **Enhanced Health Check** — `/health` now probes database connectivity, reports `ok`/`degraded`

## What's Next
- [ ] Tier 2: analytics dashboard, dynamic kickstarter rates, smarter photo rotation
- [ ] Tier 3: price randomization, bulk edit service, per-item timeline
- [x] ~~Web dashboard~~ UI prototype screens served from FastAPI
- [ ] iOS app, Android UI polish
- [ ] PostgreSQL for production deployment
- [ ] Rate limiting on API endpoints

## Timeline

### 2026-02-05
- Initialized project repository
- Created pre-project files
- Completed full architecture plan
- Built Phase 0: Project foundation (pyproject.toml, directory structure, config, models base, Alembic)
- Built Phase 1: Profit Floor Calc + Title Sanitizer (53 tests)
- Built Phase 2: All 7 database models + EbayGateway/Scheduler protocols
- Built Phase 3: Mock eBay client with fixtures (10 varied listings)
- Built Phase 4: Zombie Killer + Resurrector (32 tests)
- Built Phase 5: SmartQueue with surge window scheduling (18 tests)
- Built Phase 6: APScheduler integration with job registry
- Built Phase 7: FastAPI REST API with 7 endpoints (7 API tests)
- Built Phase 8: All remaining services — Mobile Enforcer, STR Enforcer, Store Pulse, Photo Shuffler, Kickstarter, Purgatory, Offer Sniper (99 new tests, 218 total)

### 2026-02-07
- Built Phase 9: Real eBay client — token manager, rate limiter, HTTP client, 7 endpoint modules, RealEbayClient facade (66 new tests, 284 total)

### 2026-02-08
- Tier 1 upgrades: graduated repricer, auto relister, offer sniper V2 (tiered + per-watcher cooldown + inbound handling), OfferRecord model, new API routers (349 tests)
- Connected to eBay Sandbox — credentials working

### 2026-02-09
- Android app: Expo SDK 54, React Native, 5-tab layout, API integration

### 2026-02-13
- Production readiness: API key auth, CORS lockdown, structured logging, CI/CD pipeline, Alembic initial migration, enhanced health check (355 tests)
- UI prototype screens: 5 Tailwind dark-mode pages (dashboard, onboarding, scanner results, zombie killer, A/B test) served as static files from FastAPI at `/`
