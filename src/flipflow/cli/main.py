"""FlipFlow CLI — main entry point."""

import typer

app = typer.Typer(
    name="flipflow",
    help="FlipFlow — Algorithmic Asset Manager for eBay Listings",
    no_args_is_help=True,
)


# Command groups
from flipflow.cli.commands import listings as listings_cmd
from flipflow.cli.commands import profit as profit_cmd
from flipflow.cli.commands import zombies as zombies_cmd
from flipflow.cli.commands import queue as queue_cmd

listings_app = typer.Typer(help="Listing management and validation")
zombies_app = typer.Typer(help="Zombie detection and resurrection")
queue_app = typer.Typer(help="SmartQueue management")
profit_app = typer.Typer(help="Profit calculations")
scheduler_app = typer.Typer(help="Job scheduler management")
db_app = typer.Typer(help="Database management")

# Register implemented commands
profit_app.command(name="calc")(profit_cmd.calc)
listings_app.command(name="sanitize")(listings_cmd.sanitize)
zombies_app.command(name="scan")(zombies_cmd.scan)
zombies_app.command(name="resurrect")(zombies_cmd.resurrect)
queue_app.command(name="add")(queue_cmd.add)
queue_app.command(name="release")(queue_cmd.release)
queue_app.command(name="status")(queue_cmd.status)

app.add_typer(listings_app, name="listings")
app.add_typer(zombies_app, name="zombies")
app.add_typer(queue_app, name="queue")
app.add_typer(profit_app, name="profit")
app.add_typer(scheduler_app, name="scheduler")
app.add_typer(db_app, name="db")


@app.command()
def version():
    """Show FlipFlow version."""
    from flipflow import __version__

    typer.echo(f"FlipFlow v{__version__}")


@app.callback()
def main():
    """
    FlipFlow — Algorithmic Asset Manager for eBay Listings.

    Manage your eBay inventory with automated zombie detection,
    smart queue scheduling, and profit optimization.
    """


if __name__ == "__main__":
    app()
