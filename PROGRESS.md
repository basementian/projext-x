# FlipFlow — Progress

## Current Status
**Phase:** Phase 9 Complete (real eBay client built)
**Tests:** 284 passing
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
- **Offer Sniper** — watcher polling, 10% discount offers, 24h cooldown between offers
- **REST API** — health, listings CRUD, zombie scan/resurrect, queue management
- **Mock eBay Client** — stateful in-memory mock implementing EbayGateway protocol
- **Real eBay Client** — OAuth 2.0 token manager, rate limiter with backoff, 7 endpoint modules (inventory, offers, analytics, marketing, browse, negotiation, account)
- **Scheduler** — APScheduler with job registry (zombie scan, queue release, store pulse, etc.)

## What's Next
- [ ] Configure eBay API keys and test with sandbox
- [ ] Android app (future)
- [ ] iOS app (future)
- [ ] Web dashboard (future)

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
