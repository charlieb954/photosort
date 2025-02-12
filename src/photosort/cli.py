"""cli.py - Command Line Interface for photosort."""

import typer

from .photosort import main

app = typer.Typer()
app.command()(main)


if __name__ == "__main__":
    app()
