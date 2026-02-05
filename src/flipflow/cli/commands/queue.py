"""CLI commands for SmartQueue management."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from flipflow.core.config import FlipFlowConfig
from flipflow.core.services.lifecycle.smart_queue import SmartQueue
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient
from flipflow.infrastructure.database.session import create_session_factory

console = Console()


def _get_queue():
    config = FlipFlowConfig(_env_file=None)
    ebay = MockEbayClient()
    return config, SmartQueue(ebay, config)


async def _run_add(listing_id: int, priority: int):
    config, queue = _get_queue()
    session_factory = create_session_factory(config)
    async with session_factory() as session:
        entry = await queue.enqueue(session, listing_id, priority=priority)
        await session.commit()
        return entry


async def _run_release(dry_run: bool):
    config, queue = _get_queue()
    session_factory = create_session_factory(config)
    async with session_factory() as session:
        entries = await queue.release_batch(session, dry_run=dry_run)
        if not dry_run:
            await session.commit()
        return entries, queue.is_surge_window_active()


async def _run_status():
    config, queue = _get_queue()
    session_factory = create_session_factory(config)
    async with session_factory() as session:
        return await queue.get_queue_status(session)


def add(
    listing_id: int = typer.Argument(..., help="Listing ID to add to queue"),
    priority: int = typer.Option(0, "--priority", "-p", help="Priority (higher = sooner)"),
):
    """Add a listing to the SmartQueue."""
    try:
        entry = asyncio.run(_run_add(listing_id, priority))
        console.print(f"[green]Added listing {listing_id} to queue (priority: {priority})[/]")
    except ValueError as e:
        console.print(f"[red]{e}[/]")


def release(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview what would be released"),
):
    """Release next batch of queued listings."""
    entries, surge_active = asyncio.run(_run_release(dry_run))

    if not entries:
        console.print("[yellow]No pending entries in queue.[/]")
        return

    mode = "[dim](DRY RUN)[/]" if dry_run else ""
    console.print(f"[bold]Released {len(entries)} listings {mode}[/]")

    if not surge_active:
        console.print("[yellow]Note: Surge window is NOT active right now.[/]")


def status():
    """Show SmartQueue status."""
    result = asyncio.run(_run_status())

    table = Table(title="SmartQueue Status", show_header=False)
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Pending", str(result["pending"]))
    table.add_row("Released today", str(result["released_today"]))
    table.add_row("Failed", str(result["failed"]))
    table.add_row("Total entries", str(result["total"]))

    surge_status = "[green]ACTIVE[/]" if result["surge_window_active"] else "[dim]inactive[/]"
    table.add_row("Surge window", surge_status)

    console.print(table)
