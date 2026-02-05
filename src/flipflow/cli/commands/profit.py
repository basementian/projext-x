"""CLI commands for profit calculations."""

import typer
from rich.console import Console
from rich.table import Table

from flipflow.core.config import FlipFlowConfig
from flipflow.core.schemas.profit import ProfitCalcRequest
from flipflow.core.services.gatekeeper.profit_floor import ProfitFloorCalc

console = Console()


def calc(
    price: float = typer.Option(..., "--price", "-p", help="Expected sale price"),
    cost: float = typer.Option(..., "--cost", "-c", help="Purchase cost"),
    shipping: float = typer.Option(0, "--shipping", "-s", help="Shipping cost"),
    ad_rate: float = typer.Option(0, "--ad-rate", "-a", help="Ad rate percentage (e.g. 1.5)"),
):
    """Calculate net profit after all eBay fees."""
    config = FlipFlowConfig(_env_file=None)
    calc = ProfitFloorCalc(config)
    request = ProfitCalcRequest(
        sale_price=price,
        purchase_price=cost,
        shipping_cost=shipping,
        ad_rate_percent=ad_rate,
    )
    result = calc.calculate(request)

    table = Table(title="Profit Breakdown", show_header=False)
    table.add_column("Label", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Sale Price", f"${result.sale_price:.2f}")
    table.add_row("Purchase Cost", f"-${result.purchase_price:.2f}")
    table.add_row("Shipping", f"-${result.shipping_cost:.2f}")
    table.add_row("", "")
    table.add_row(f"eBay Fee ({result.ebay_fee_rate:.0%})", f"-${result.ebay_fee_amount:.2f}")
    table.add_row(f"Ad Fee ({result.ad_rate_percent}%)", f"-${result.ad_fee_amount:.2f}")
    table.add_row("Payment Processing", f"-${result.payment_processing_amount:.2f}")
    table.add_row("", "───────")
    table.add_row("Total Fees", f"-${result.total_fees:.2f}")
    table.add_row("", "")

    profit_style = "green bold" if result.meets_floor else "red bold"
    table.add_row("Net Profit", f"${result.net_profit:.2f}", style=profit_style)
    table.add_row("Margin", f"{result.profit_margin_percent:.1f}%")

    console.print(table)

    if not result.meets_floor:
        console.print(
            f"\n[red bold]RED ALERT:[/] Profit ${result.net_profit:.2f} "
            f"is below ${result.profit_floor:.2f} floor!"
        )
        console.print(
            f"[yellow]Minimum viable price:[/] ${result.minimum_viable_price:.2f}"
        )
    else:
        console.print(f"\n[green]Profit meets ${result.profit_floor:.2f} floor.[/]")
