# api/ — FastAPI REST API

## Rules
- Routers go in `routers/`. One file per domain (listings, zombies, queue, etc.).
- All endpoints are under `/api/v1/` prefix.
- NEVER put business logic in routers. Call services from `core/services/`.
- Dependencies (DB session, config, eBay client) are injected via `dependencies.py`.

## Structure
- `app.py` — App factory (`create_app`), middleware registration, router includes, static file mounting.
- `dependencies.py` — FastAPI `Depends()` providers for DB session, config, eBay gateway.
- `middleware.py` — API key auth, CORS, logging middleware.
- `routers/` — Endpoint definitions. Each router gets injected dependencies, calls services, returns Pydantic schemas.

## Conventions
- Health endpoint (`/api/v1/health`) is public, no auth required.
- All other endpoints require `X-API-Key` header.
- Use Pydantic response models for all endpoints.
- Keep routers thin — validate input, call service, return response.
