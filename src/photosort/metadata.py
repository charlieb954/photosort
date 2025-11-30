"""Module for extracting metadata and timestamps from media files."""

import datetime
import logging
import re
from pathlib import Path
from typing import Optional

from exiftool import ExifToolHelper


def get_date_taken(
    helper: ExifToolHelper, filepath: Path
) -> Optional[datetime.datetime]:
    """
    Finds the creation date of a media file.

    Returns:
        Datetime object if found, otherwise None.
    """
    target_tags = [
        "Composite:SubSecDateTimeOriginal",
        "EXIF:DateTimeOriginal",
        "QuickTime:CreationDate",
        "QuickTime:CreateDate",
        "QuickTime:MediaCreateDate",
        "File:FileModifyDate",
    ]

    try:
        tags = helper.get_tags(str(filepath), target_tags)[0]

        # Strategy 1: Metadata Tags
        metadata_candidates = [
            tags.get("Composite:SubSecDateTimeOriginal"),
            tags.get("EXIF:DateTimeOriginal"),
            tags.get("QuickTime:CreationDate"),
            tags.get("QuickTime:CreateDate"),
            tags.get("QuickTime:MediaCreateDate"),
        ]

        for date_str in metadata_candidates:
            if date_str:
                clean_date = str(date_str)[:19]
                try:
                    return datetime.datetime.strptime(
                        clean_date, "%Y:%m:%d %H:%M:%S"
                    )
                except ValueError:
                    continue

        # Strategy 2: Filename Regex
        filename_pattern = re.search(
            r"(20[0-2][0-9])[:_-]?(\d{2})[:_-]?(\d{2})", filepath.name
        )
        if filename_pattern:
            y, m, d = filename_pattern.groups()
            return datetime.datetime(int(y), int(m), int(d), 12, 0, 0)

        # Strategy 3: File System (Last Resort)
        fs_date = tags.get("File:FileModifyDate")
        if fs_date:
            return datetime.datetime.strptime(
                str(fs_date)[:19], "%Y:%m:%d %H:%M:%S"
            )

    except Exception as e:
        logging.error(f"Metadata error for {filepath}: {e}")
        pass

    return None
