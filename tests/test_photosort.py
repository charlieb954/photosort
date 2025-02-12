"""tests for photosort module"""

import shutil
from pathlib import Path

import pytest

from photosort.photosort import (
    copy_and_rename_file,
    extract_exif_metadata,
    find_photos,
    generate_file_hash,
)


@pytest.fixture
def photo_name() -> str:
    """photo name fixture for testing"""
    return "Canon_40D.jpg"


@pytest.fixture
def test_photos() -> Path:
    """photos folder fixture for testing"""
    return Path("./data/test-photos")


def test_find_photos(test_photos: Path) -> None:
    """test find_photos function"""
    assert test_photos.exists()
    assert isinstance(find_photos(test_photos), list)


def test_extract_exif_metadata(test_photos: Path, photo_name: str) -> None:
    """test extract_exif_metadata function"""
    src_path = test_photos / photo_name
    metadata = extract_exif_metadata(str(src_path))

    assert metadata["filename"] == photo_name
    assert metadata["image-size"] == (100, 68)
    assert metadata["image-format"] == "JPEG"
    assert metadata["image-mode"] == "RGB"


def test_generate_file_hash(test_photos: Path, photo_name: str) -> None:
    """test generate_file_hash function"""
    src_path = test_photos / photo_name
    photo_hash = generate_file_hash(str(src_path))

    assert len(photo_hash) == 32  # MD5 hash length is 32 characters


def test_copy_rename_file(test_photos: Path, photo_name: str) -> None:
    """test copy_and_rename_file function"""
    src_path = test_photos / photo_name
    dest_folder = test_photos / "test-destination"
    filename, ext = photo_name.split(".")
    dest_path = dest_folder / f"{filename}_000.{ext}"

    assert copy_and_rename_file(
        src_path=src_path,
        dest_folder=dest_folder,
        filename=filename,
        ext=f".{ext}",
    )
    assert dest_path.exists()

    # Clean up
    shutil.rmtree(dest_folder)
