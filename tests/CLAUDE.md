# tests/ — Test Suite

## Rules
- All tests use `pytest` with `asyncio_mode = "auto"`.
- Run with: `.venv/bin/python -m pytest tests/ -v`
- NEVER use `source .venv/bin/activate` — use the full `.venv/bin/python` path.

## Structure
- `unit/` — Service logic tests. Mock everything external. Fast.
- `integration/` — Database + multi-service tests. Use real SQLite.
- `api/` — HTTP endpoint tests via `httpx.AsyncClient`.
- `conftest.py` — Shared fixtures (mock eBay client, DB session, test config).

## Conventions
- New services must have unit tests before merging.
- Use `MockEbayClient` from `infrastructure/ebay_mock/` for all eBay interactions in tests.
- Test file naming: `test_{service_name}.py`.
- Each test should be independent — no shared mutable state between tests.
- Pre-commit runs `tests/unit` only (fast gate). CI runs everything.
