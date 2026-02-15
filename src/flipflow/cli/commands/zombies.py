"""CLI commands for zombie detection and resurrection."""

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from flipflow.core.config import FlipFlowConfig
from flipflow.core.services.lifecycle.resurrector import Resurrector
from flipflow.core.services.lifecycle.zombie_killer import ZombieKiller
from flipflow.infrastructure.database.session import create_session_factory
from flipflow.infrastructure.ebay_mock.mock_client import MockEbayClient

console = Console()


def _get_services():
    config = FlipFlowConfig(_env_file=None)
    ebay = MockEbayClient()
    return config, ebay, ZombieKiller(ebay, config), Resurrector(ebay, config)


async def _run_scan():
    config, ebay, killer, _ = _get_services()
    session_factory = create_session_factory(config)
    async with session_factory() as session:
        result = await killer.scan(session)
        return result


async def _run_resurrect(listing_id: int):
    config, ebay, killer, resurrector = _get_services()
    session_factory = create_session_factory(config)
    async with session_factory() as session:
        result = await resurrector.resurrect(session, listing_id)
        await session.commit()
        return result


def scan():
    """Scan active listings for zombies (>60 days, <10 views)."""
    result = asyncio.run(_run_scan())

    if result.zombies_found == 0:
        console.print(f"[green]Scanned {result.total_scanned} listings. No zombies found.[/]")
        return

    table = Table(title=f"Zombie Report — {result.zombies_found} found")
    table.add_column("ID", style="dim")
    table.add_column("SKU")
    table.add_column("Title")
    table.add_column("Days", justify="right")
    table.add_column("Views", justify="right")
    table.add_column("Cycles", justify="right")
    table.add_column("Status")

    for z in result.zombies:
        status = "[red]PURGATORY[/]" if z.should_purgatory else "[yellow]ZOMBIE[/]"
        table.add_row(
            str(z.listing_id),
            z.sku,
            z.title[:35],
            str(z.days_active),
            str(z.total_views),
            str(z.zombie_cycle_count),
            status,
        )

    console.print(table)
    console.print(
        f"\n[dim]Scanned: {result.total_scanned} | "
        f"Zombies: {result.zombies_found} | "
        f"Purgatory candidates: {result.purgatory_candidates}[/]"
    )


def resurrect(
    listing_id: int = typer.Argument(..., help="Listing ID to resurrect"),
):
    """Resurrect a zombie listing with a fresh Item ID."""
    result = asyncio.run(_run_resurrect(listing_id))

    if result.success:
        console.print("[green bold]Resurrected![/]")
        console.print(f"  Old Item ID: {result.old_item_id}")
        console.print(f"  New Item ID: {result.new_item_id}")
        console.print(f"  New SKU:     {result.sku}")
        console.print(f"  Cycle:       {result.cycle_number}")
    else:
        console.print(f"[red bold]Resurrection failed:[/] {result.error}")
