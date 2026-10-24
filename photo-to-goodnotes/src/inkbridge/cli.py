"""Command-line entry point for future pipeline operations."""

import typer

app = typer.Typer(help="InkBridge project scaffold. Conversion is not implemented yet.")


@app.command()
def status() -> None:
    """Show the implementation state of this scaffold."""
    typer.echo("InkBridge scaffold installed. Conversion is not implemented yet.")


def main() -> None:
    app()
