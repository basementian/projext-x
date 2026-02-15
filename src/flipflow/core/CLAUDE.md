# core/ — Business Logic Layer

## Rules
- NEVER import from `infrastructure/` or `api/` or `cli/`. This layer is UI-agnostic.
- Depend on protocols (`core/protocols/`), never on concrete implementations.
- All services accept an `EbayGateway` protocol, not `MockEbayClient` or `RealEbayClient`.

## Structure
- `models/` — SQLAlchemy ORM models (9 tables). Base in `base.py` with TimestampMixin and SoftDeleteMixin.
- `schemas/` — Pydantic request/response models. Keep separate from ORM models.
- `services/` — Business logic. Two sub-packages:
  - `gatekeeper/` — Validation services (profit floor, title sanitizer, mobile enforcer, STR enforcer)
  - `lifecycle/` — Automation services (zombie killer, resurrector, smart queue, repricer, etc.)
- `protocols/` — Abstract interfaces. `EbayGateway` is the main one.
- `config.py` — App settings via pydantic-settings.
- `constants.py` — Magic numbers and thresholds (fee rates, day limits, etc.).
- `exceptions.py` — Domain-specific exceptions.

## Conventions
- Services are plain classes, instantiated with dependencies passed in `__init__`.
- All async. Use `async def` for any method that touches the eBay gateway or DB.
- Thresholds and rates live in `constants.py`, not hardcoded in services.
