"""CLI commands for listing management."""

import typer
from rich.console import Console

from flipflow.core.schemas.title import TitleSanitizeRequest
from flipflow.core.services.gatekeeper.title_sanitizer import TitleSanitizer

console = Console()


def sanitize(
    title: str = typer.Argument(..., help="Raw listing title to sanitize"),
    brand: str = typer.Option(None, "--brand", "-b", help="Brand name to front-load"),
    model: str = typer.Option(None, "--model", "-m", help="Model name to front-load"),
):
    """Sanitize a listing title for Cassini SEO optimization."""
    sanitizer = TitleSanitizer()
    request = TitleSanitizeRequest(title=title, brand=brand, model=model)
    result = sanitizer.sanitize(request)

    console.print(f"\n[dim]Original:[/]  {result.original}")
    console.print(f"[bold green]Cleaned:[/]   {result.sanitized}")
    console.print(f"[dim]Length:[/]    {result.length}/80")

    if result.changes and result.changes[0] != "No changes needed":
        console.print("\n[yellow]Changes made:[/]")
        for change in result.changes:
            console.print(f"  - {change}")

    if result.brand_model_in_front:
        console.print("[green]Brand/Model in first 30 chars.[/]")
    elif brand or model:
        console.print("[yellow]Warning: Brand/Model NOT in first 30 chars.[/]")
