# Contributing to flipflow

Thanks for taking the time to contribute.

## Development setup

1. Install Python 3.12.
2. Install [uv](https://docs.astral.sh/uv/).
3. Create dependencies:

```bash
uv sync --all-extras
```

4. Copy env template:

```bash
cp .env.example .env
```

## Local quality checks

Run the same checks used in CI before opening a PR:

```bash
uv run ruff check src/ tests/
uv run pytest tests/ -v --tb=short
uv run mypy src/flipflow/ --ignore-missing-imports
```

## Commit and PR guidance

- Keep commits focused and small.
- Prefer descriptive commit messages in imperative mood (e.g., `Add API retry guard`).
- Include tests for behavioral changes.
- Update docs when you change behavior, configuration, or commands.

## Project structure

- `src/flipflow/`: backend application code.
- `tests/`: unit, integration, and API tests.
- `alembic/`: database migration scripts.
- `flipflow-android/`: mobile client.
- `ui/`: static UI prototypes/assets.

## Reporting issues

Please use issue templates and include:

- What happened.
- What you expected.
- Steps to reproduce.
- Logs or screenshots when relevant.
