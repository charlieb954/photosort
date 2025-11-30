"""Main command-line interface for Photosort using Typer."""

import collections
import datetime
import logging
from pathlib import Path
from typing import Annotated, Optional

import typer
from exiftool import ExifToolHelper
from rich import console as rich_console
from rich import panel, progress, table

from . import metadata, utils

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".heic",
    ".heif",
    ".mov",
    ".mp4",
    ".m4v",
}

CONSOLE = rich_console.Console(force_jupyter=False)
app = typer.Typer(
    name="photosort", help="Organize media files.", add_completion=False
)


def setup_logging(log_file: Path) -> None:
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        filemode="w",
        force=True,
    )


# --- ACTION HANDLERS ---


def _handle_rename(
    file_path: Path, date_obj: Optional[datetime.datetime]
) -> tuple[str, bool]:
    """Renames file. Returns (msg, success)."""
    if not date_obj:
        logging.warning(f"SKIPPED (No Date): {file_path}")
        return f"[dim red]No Date: {file_path.name}[/]", False

    new_name = utils.generate_filename(date_obj, file_path)
    if new_name == file_path.name:
        return f"[dim]Name OK: {file_path.name}[/]", False

    final_name, performed = utils.copy_with_rename(
        file_path, file_path.parent, new_name, move_operation=True
    )

    if performed:
        logging.info("RENAMED: %s -> %s", file_path.name, final_name)
        return f"[green]Renamed: {final_name}[/]", True
    return f"[dim]Skipped: {final_name}[/]", False


def _handle_fix(
    file_path: Path, dest: Path, date_obj: Optional[datetime.datetime]
) -> tuple[str, bool]:
    """Sorts file. Returns (msg, success)."""
    folder_name = date_obj.strftime("%Y-%m") if date_obj else "Unknown_Date"
    target_folder = dest / folder_name
    target_folder.mkdir(parents=True, exist_ok=True)

    new_name = utils.generate_filename(date_obj, file_path)
    final_name, performed = utils.copy_with_rename(
        file_path, target_folder, new_name, move_operation=False
    )

    if performed:
        logging.info(
            "COPIED: %s -> %s/%s", file_path, target_folder, final_name
        )
        return f"[green]Copied: {final_name}[/]", True

    return f"[dim]Exists in Dest: {final_name}[/]", False


def _should_skip_file(
    file_path: Path, skip_sorted: bool, valid_exts: set[str]
) -> tuple[bool, str]:
    if skip_sorted and utils.is_folder_sorted(file_path):
        return True, "sorted"
    if file_path.suffix.lower() not in valid_exts:
        return True, "extension"
    return False, ""


# --- MAIN LOGIC ---


def process_media(
    source: Path, dest: Optional[Path], mode: str, skip_sorted: bool = True
) -> tuple[dict, collections.Counter]:
    stats = {
        "processed": 0,
        "duplicates": 0,
        "errors": 0,
        "skipped_ext": 0,
        "skipped_sorted": 0,
        "skipped_dest": 0,  # <--- NEW STAT
    }
    ignored_extensions = collections.Counter()
    seen_hashes = set()

    all_files = sorted(
        [
            p
            for p in source.rglob("*")
            if p.is_file() and not p.name.startswith(".")
        ],
        reverse=True,
    )

    if not all_files:
        return stats, ignored_extensions

    with ExifToolHelper() as et:
        with progress.Progress(
            progress.SpinnerColumn(),
            progress.TextColumn("[progress.description]{task.description}"),
            progress.BarColumn(),
            progress.TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%"
            ),
            progress.TimeRemainingColumn(),
            console=CONSOLE,
        ) as bar:
            task = bar.add_task("[cyan]Processing...", total=len(all_files))

            for file_path in all_files:
                try:
                    # 1. Validity Checks
                    should_skip, reason = _should_skip_file(
                        file_path, skip_sorted, VALID_EXTENSIONS
                    )

                    if should_skip:
                        if reason == "sorted":
                            stats["skipped_sorted"] += 1
                            if stats["skipped_sorted"] % 10 == 0:
                                bar.update(
                                    task,
                                    advance=1,
                                    description=f"[dim]Skipping sorted: {file_path.parent.name}[/]",
                                )
                            else:
                                bar.update(task, advance=1)
                        elif reason == "extension":
                            ext = file_path.suffix.lower()
                            ignored_extensions[ext] += 1
                            stats["skipped_ext"] += 1
                            bar.update(
                                task,
                                advance=1,
                                description=f"[dim]Ignored: {ext}[/]",
                            )
                        continue

                    # 2. Duplicate Check (Source)
                    file_hash = utils.get_file_hash(file_path)
                    if file_hash in seen_hashes:
                        stats["duplicates"] += 1
                        logging.info("DUPLICATE FOUND: %s", file_path)
                        bar.update(
                            task,
                            advance=1,
                            description=f"[yellow]Dup: {file_path.name}[/]",
                        )
                        continue
                    seen_hashes.add(file_hash)

                    # 3. Metadata
                    date_obj = metadata.get_date_taken(et, file_path)

                    # 4. Action Dispatch
                    match mode:
                        case "count":
                            stats["processed"] += 1
                            bar.update(
                                task,
                                advance=1,
                                description=f"[blue]Valid: {file_path.name}[/]",
                            )

                        case "rename":
                            msg, performed = _handle_rename(
                                file_path, date_obj
                            )
                            if performed:
                                stats["processed"] += 1
                            bar.update(task, advance=1, description=msg)

                        case "fix":
                            if not dest:
                                raise ValueError(
                                    "Dest must be provided for fix mode"
                                )
                            msg, performed = _handle_fix(
                                file_path, dest, date_obj
                            )
                            if performed:
                                stats["processed"] += 1
                            else:
                                stats["skipped_dest"] += (
                                    1  # <--- Track Existing
                                )
                            bar.update(task, advance=1, description=msg)

                        case _:
                            raise ValueError(f"Unknown mode: {mode}")

                except Exception as e:
                    stats["errors"] += 1
                    logging.error("ERROR %s: %s", file_path, e)
                    bar.update(task, advance=1)

    return stats, ignored_extensions


def print_summary(stats: dict, ignored: collections.Counter, title: str):
    summary = table.Table(title=title)
    summary.add_column("Metric", style="cyan")
    summary.add_column("Count", style="magenta")

    summary.add_row("Files Actually Copied", str(stats["processed"]))
    summary.add_row(
        "Skipped (Already in Dest)", str(stats["skipped_dest"])
    )  # <--- NEW ROW
    summary.add_row("Skipped (Source Sorted)", str(stats["skipped_sorted"]))
    summary.add_row("Duplicates (Source)", str(stats["duplicates"]))
    summary.add_row("Ignored Types", str(stats["skipped_ext"]))
    summary.add_row("Errors", str(stats["errors"]))
    CONSOLE.print(summary)


# ... COMMANDS (count, rename, fix) remain the same ...
# Just make sure they call process_media and print_summary
@app.command()
def count(
    source: Annotated[
        Path, typer.Option("--source", "-s", exists=True, file_okay=False)
    ],
    log: Annotated[Path, typer.Option("--log", "-l")] = Path("photosort.log"),
    check_sorted: Annotated[
        bool,
        typer.Option(
            "--check-sorted/--skip-sorted",
            help="Analyze folders that already look sorted?",
        ),
    ] = False,
):
    setup_logging(log)
    CONSOLE.print(
        panel.Panel(f"Analyzing [bold blue]{source}[/]", title="Count")
    )
    stats, ignored = process_media(
        source, None, mode="count", skip_sorted=not check_sorted
    )
    print_summary(stats, ignored, "Analysis Report")


@app.command()
def rename(
    source: Annotated[
        Path, typer.Option("--source", "-s", exists=True, file_okay=False)
    ],
    log: Annotated[Path, typer.Option("--log", "-l")] = Path("photosort.log"),
):
    setup_logging(log)
    CONSOLE.print(
        panel.Panel(
            f"Renaming files in [bold blue]{source}[/]", title="Rename Only"
        )
    )
    stats, ignored = process_media(
        source, None, mode="rename", skip_sorted=False
    )
    print_summary(stats, ignored, "Rename Complete")


@app.command()
def fix(
    source: Annotated[Path, typer.Option("--source", "-s", exists=True)],
    dest: Annotated[
        Path, typer.Option("--dest", "-d", file_okay=False, writable=True)
    ],
    log: Annotated[Path, typer.Option("--log", "-l")] = Path("photosort.log"),
    force_resort: Annotated[
        bool,
        typer.Option(
            "--force", help="Process files even if they are in Year-folders."
        ),
    ] = False,
):
    setup_logging(log)
    CONSOLE.print(
        panel.Panel(
            f"Sorting [bold blue]{source}[/] -> [bold green]{dest}[/]",
            title="Fix",
        )
    )
    stats, ignored = process_media(
        source, dest, mode="fix", skip_sorted=not force_resort
    )
    print_summary(stats, ignored, "Sort Complete")


def main():
    app()


if __name__ == "__main__":
    main()
