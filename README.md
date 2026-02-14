# flipflow

Algorithmic asset manager for eBay listings.

## Repository layout

- `src/flipflow/`: backend services, API, and CLI.
- `tests/`: unit, integration, and API tests.
- `alembic/`: database migrations.
- `flipflow-android/`: mobile app code.
- `ui/`: static UI prototypes/screens.

## Quick start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

### Install

```bash
uv sync --all-extras
cp .env.example .env
```

### Run checks

```bash
uv run ruff check src/ tests/
uv run pytest tests/ -v --tb=short
uv run mypy src/flipflow/ --ignore-missing-imports
```

## CI

GitHub Actions runs linting, tests, and type checking on pull requests and pushes to `main`.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). For the folder-by-folder 5-batch standardization plan, see [docs/ENGINEERING_STANDARDS.md](./docs/ENGINEERING_STANDARDS.md).

## Security

See [SECURITY.md](./SECURITY.md).

## Code of Conduct

See [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
