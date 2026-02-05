# FlipFlow

## Overview
Algorithmic Asset Manager for eBay Listings. Python 3.12, FastAPI REST API, Typer CLI, SQLAlchemy async, SQLite (MVP), Mock eBay client for development.

## Architecture
- `src/flipflow/core/` — UI-agnostic business logic (models, schemas, protocols, services)
- `src/flipflow/infrastructure/` — Concrete implementations (database, eBay clients, scheduler)
- `src/flipflow/api/` — FastAPI REST API
- `src/flipflow/cli/` — Typer CLI
- `tests/` — unit, integration, api test layers

## Key Patterns
- **EbayGateway protocol** (`core/protocols/ebay_gateway.py`): Every service depends on this, never on a concrete eBay client.
- **MockEbayClient** (`infrastructure/ebay_mock/mock_client.py`): Stateful mock for all testing.
- **Services never import from infrastructure directly** — dependency injection via protocol.

## Conventions
- Update PROGRESS.md whenever something is built or changed.
- All tests use `pytest` with `asyncio_mode = "auto"`.
- Run tests: `.venv/bin/python -m pytest tests/ -v`
- Run CLI: `.venv/bin/python -m flipflow` or `flipflow` (if venv active)
- Run API: `.venv/bin/python -m uvicorn flipflow.api.app:create_app --factory`

## Environment
- Python 3.12.12 via uv (`/Users/ianaliam/.local/bin/uv`)
- Virtual env: `.venv/`
- Use `.venv/bin/python -m pytest` to run tests (avoid `source .venv/bin/activate` which can fail in non-interactive shells)
