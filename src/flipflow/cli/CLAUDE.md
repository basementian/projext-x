# cli/ — Typer CLI

## Rules
- CLI is a thin wrapper. Call services from `core/services/`, don't duplicate logic.
- Commands go in `commands/`. One file per domain.
- Register command groups in `main.py`.

## Structure
- `main.py` — Typer app, registers all command groups.
- `commands/` — Individual command files (profit, listings, zombies, queue, scheduler, db).

## Conventions
- Use Rich for table/panel output (already a dependency).
- Commands that need DB/eBay client must create their own session (no FastAPI DI here).
- Use `typer.Option` for flags, `typer.Argument` for required positional args.
- Keep output concise — tables for lists, panels for single items.
