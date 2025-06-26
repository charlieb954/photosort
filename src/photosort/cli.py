"""cli.py - Command Line Interface for photosort."""

import typer

from .photosort import main, count_duplicates

app = typer.Typer(
    help="photsort: Organise and sort photos easily from the command line.",
)


@app.command(help="Run the main photo sorting operation.")
def run(
    src: str = typer.Argument(..., help="Source directory of photos."),
    dest: str = typer.Argument(
        ..., help="Destination directory for sorted photos."
    ),
) -> None:
    """run the main photosort function."""
    main(src=src, dest=dest)


@app.command(
    help="Count the number of duplicate photos in the src/ directory."
)
def count(
    src: str = typer.Argument(..., help="Source directory of photos."),
) -> None:
    """run the main photosort count duplicates function."""
    count_duplicates(src=src)


if __name__ == "__main__":
    app()
