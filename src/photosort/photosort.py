"""This script sorts photos based on their EXIF metadata."""

import hashlib
import logging
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import typer
from PIL import ExifTags, Image
from pillow_heif import register_heif_opener
from typing_extensions import Annotated

register_heif_opener()  # Register HEIC support for Pillow
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

SUPPORTED_FILE_TYPES = (".jpg", ".jpeg", ".heic", ".tiff", ".heif")


def copy_and_rename_file(
    src_path: str, dest_folder: str, filename: str, ext: str
) -> None:
    """copies a file, renames it, and moves it to another folder.

    Args:
        src_path (str): The full path of the source file.
        dest_folder (str): The destination folder where the file will be moved.
        filename (str): The new name for the file (NOT including extension).
        ext (str): The file extension.
    """
    try:
        # Ensure the destination folder exists, creating it if necessary
        Path(dest_folder).mkdir(parents=True, exist_ok=True)

        # Construct the destination file path
        new_name = f"{filename}_000{ext}"
        dest_path = Path(dest_folder) / new_name

        # Increment filename if it already exists
        counter = 1
        while Path(dest_path).exists():
            new_name = f"{filename}_{counter:03d}{ext}"
            dest_path = Path(dest_folder) / new_name
            counter += 1

        # Copy the file to the destination folder
        shutil.copy(src_path, dest_path)

        return True

    except Exception as e:
        logging.error(f"Error copying file: {e}")
        return False


def extract_exif_metadata(file_path: str) -> dict:
    """extract EXIF metadata from an image or video file.

    Args:
        file_path (str): The path to the image or video file.

    Returns:
        dict: A dictionary of metadata values.
    """
    metadata = {}
    with Image.open(file_path) as image:
        metadata.update(
            {
                "filename": os.path.basename(file_path),
                "image-size": image.size,
                "image-format": image.format,
                "image-mode": image.mode,
            }
        )
        exif_data = image.getexif()

    if exif_data:
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            if isinstance(value, bytes):
                value = value.decode(errors="ignore")
            metadata[tag] = value

    return metadata


def hash_extract_metadata(photo_paths: list) -> tuple[list, int]:
    """hash the photos and extract their metadata.

    Args:
        photo_paths (list): a list of photo paths.

    Returns:
        dict: photos metadata.
        int: duplicate count.
    """
    photos_metadata = defaultdict(dict)
    duplicate_count = 0

    for file_path in photo_paths:
        photo_hash = generate_file_hash(file_path)
        if photo_hash in photos_metadata.keys():
            logging.info(
                f"Duplicate file found: {file_path} (hash: {photo_hash})"
            )
            duplicate_count += 1
        else:
            metadata = extract_exif_metadata(file_path)
            photos_metadata[photo_hash]["metadata"] = metadata

    return photos_metadata, duplicate_count


def find_photos(filepath: str) -> list:
    """find photos in a folder. TODO: add support for subfolders.

    Args:
        filepath (str): The path to the folder.

    Returns:
        list: A list of photo paths.
    """
    photo_paths = []

    for entry in Path(filepath).iterdir():
        if entry.is_file() and entry.suffix.lower() in SUPPORTED_FILE_TYPES:
            photo_paths.append(str(entry))

    return photo_paths


def generate_file_hash(file_path: str) -> str:
    """generate a hash for the file to check uniqueness.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The MD5 hash of the file.
    """
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def main(
    input_folder: Annotated[
        str, typer.Argument(help="The folder containing the original photos.")
    ],
    output_folder: Annotated[
        str, typer.Argument(help="The folder to copy the newly named photos.")
    ],
) -> None:
    """sort photos based on their EXIF metadata.

    Args:
        folder (Annotated[ str, typer.Argument )]: The folder containing the
            original photos.
        output_folder (Annotated[ str, typer.Argument )]: The folder to copy
            the newly named photos.
    """
    photos_copied = 0
    photo_paths = find_photos(input_folder)

    if photo_paths == []:
        raise Exception("No valid photos found in the input folder.")

    logging.info(f"Found {len(photo_paths)} photos.")

    photos_metadata, duplicate_count = hash_extract_metadata(photo_paths)
    if duplicate_count > 0:
        logging.warning(
            f"Found {duplicate_count} duplicate photos. "
            "Duplicates will be ignored."
        )
    else:
        logging.info("No duplicates found.")

    for photo_hash in photos_metadata.keys():
        filename = photos_metadata[photo_hash]["metadata"].get("filename")
        original_photo = Path(input_folder) / filename
        ext = original_photo.suffix.lower()

        datetime_string = photos_metadata[photo_hash]["metadata"].get(
            "DateTime", None
        )

        if not datetime_string:
            logging.warning(
                f"DateTime not found for file: {original_photo}, skipping."
            )
            continue

        try:
            date_object = datetime.strptime(
                datetime_string, "%Y:%m:%d %H:%M:%S"
            )
            year = date_object.year
            new_filename = date_object.strftime("%Y-%m-%d")
        except ValueError:
            logging.warning(
                f"Invalid DateTime format for file: {original_photo}, "
                "skipping."
            )
            continue

        copied = copy_and_rename_file(
            src_path=original_photo,
            dest_folder=Path(output_folder) / str(year),
            filename=new_filename,
            ext=f".{ext}",
        )

        if copied:
            photos_copied += 1

    logging.info(f"Finished copying {photos_copied} photos.")
