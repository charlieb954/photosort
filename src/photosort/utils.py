"""Utility functions for file hashing and filesystem operations."""

import datetime
import hashlib
import logging
import re
import shutil
from pathlib import Path
from typing import Optional, Tuple


def is_folder_sorted(path: Path) -> bool:
    """Checks if the immediate parent folder starts with a 4-digit year."""
    parent_name = path.parent.name
    return bool(re.match(r"^(19|20)\d{2}", parent_name))


def get_file_hash(filepath: Path) -> str:
    """Calculates SHA-256 hash in chunks."""
    hasher = hashlib.sha256()
    try:
        with filepath.open("rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except OSError:
        return ""


def generate_filename(
    date_obj: Optional[datetime.datetime], original_path: Path
) -> str:
    """Generates standardized filename."""
    if not date_obj:
        return original_path.name

    timestamp = date_obj.strftime("%Y-%m-%d")
    clean_stem = original_path.stem
    if clean_stem.startswith(timestamp):
        clean_stem = clean_stem[len(timestamp) :].lstrip("_-")

    clean_original = clean_stem.replace(" ", "_")
    return f"{timestamp}_{clean_original}{original_path.suffix}"


def copy_with_rename(
    source: Path,
    dest_folder: Path,
    new_filename: str,
    move_operation: bool = False,
) -> Tuple[str, bool]:
    """
    Copies/Moves file.
    Returns: (final_filename, performed_action)
        performed_action is True if file was copied/moved.
        performed_action is False if file was skipped (identical exists).
    """
    dest_path = dest_folder / new_filename

    counter = 1
    while dest_path.exists():
        # A. Identity Check (Same Path)
        if dest_path.resolve() == source.resolve():
            return dest_path.name, False

        # B. Content Check (Smart Skip)
        if get_file_hash(dest_path) == get_file_hash(source):
            logging.info(f"SKIPPED (Identical exists): {dest_path.name}")
            if move_operation:
                try:
                    source.unlink()
                except OSError:
                    pass
                return (
                    dest_path.name,
                    True,
                )  # Technically we acted (deleted source)
            return dest_path.name, False  # Copy mode: We did nothing

        # C. Collision (Rename)
        stem = dest_path.stem
        if len(stem) > 2 and stem[-2] == "_" and stem[-1].isdigit():
            stem = stem[:-2]
        dest_path = dest_folder / f"{stem}_{counter}{dest_path.suffix}"
        counter += 1

    # Perform Action
    if move_operation:
        shutil.move(source, dest_path)
    else:
        shutil.copy2(source, dest_path)

    return dest_path.name, True
