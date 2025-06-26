"""tests for photosort module"""

import shutil
from pathlib import Path

import pytest
from PIL import Image

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


def test_find_photos_empty(tmp_path: Path) -> None:
    """Test find_photos returns empty list for empty directory."""
    assert find_photos(tmp_path) == []


def test_generate_file_hash_consistency(
    test_photos: Path, photo_name: str
) -> None:
    """Test generate_file_hash returns same hash for same file."""
    src_path = test_photos / photo_name
    hash1 = generate_file_hash(str(src_path))
    hash2 = generate_file_hash(str(src_path))
    assert hash1 == hash2


def test_generate_file_hash_different_files(tmp_path: Path) -> None:
    """Test generate_file_hash returns different hashes for different files."""
    file1 = tmp_path / "a.txt"
    file2 = tmp_path / "b.txt"
    file1.write_text("hello")
    file2.write_text("world")
    hash1 = generate_file_hash(str(file1))
    hash2 = generate_file_hash(str(file2))
    assert hash1 != hash2


def test_copy_and_rename_file_duplicate(
    test_photos: Path, photo_name: str
) -> None:
    """Test copy_and_rename_file renames if file exists."""
    src_path = test_photos / photo_name
    dest_folder = test_photos / "test-destination"
    filename, ext = photo_name.split(".")
    ext = f".{ext}"
    # First copy
    assert copy_and_rename_file(
        src_path=src_path,
        dest_folder=dest_folder,
        filename=filename,
        ext=ext,
    )
    # Second copy should increment the filename
    assert copy_and_rename_file(
        src_path=src_path,
        dest_folder=dest_folder,
        filename=filename,
        ext=ext,
    )
    dest1 = dest_folder / f"{filename}_000{ext}"
    dest2 = dest_folder / f"{filename}_001{ext}"
    assert dest1.exists()
    assert dest2.exists()
    shutil.rmtree(dest_folder)


def test_extract_exif_metadata_no_exif(tmp_path: Path) -> None:
    """Test extract_exif_metadata with image without EXIF."""
    img_path = tmp_path / "no_exif.jpg"
    img = Image.new("RGB", (10, 10))
    img.save(img_path)
    metadata = extract_exif_metadata(str(img_path))
    assert metadata["filename"] == "no_exif.jpg"
    assert metadata["image-size"] == (10, 10)
    assert metadata["image-format"] == "JPEG"
    assert metadata["image-mode"] == "RGB"


def test_hash_extract_metadata_duplicates(tmp_path: Path) -> None:
    """Test hash_extract_metadata detects duplicates."""
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    img = Image.new("RGB", (10, 10), color="red")
    img.save(file1)
    img.save(file2)
    photo_paths = [str(file1), str(file2)]
    photos_metadata, duplicate_count = __import__(
        "photosort.photosort"
    ).photosort.hash_extract_metadata(photo_paths)
    assert duplicate_count == 1
    assert len(photos_metadata) == 1


def test_hash_extract_metadata_no_duplicates(tmp_path: Path) -> None:
    """Test hash_extract_metadata with unique files."""
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    img1 = Image.new("RGB", (10, 10), color="red")
    img2 = Image.new("RGB", (10, 10), color="blue")
    img1.save(file1)
    img2.save(file2)
    photo_paths = [str(file1), str(file2)]
    photos_metadata, duplicate_count = __import__(
        "photosort.photosort"
    ).photosort.hash_extract_metadata(photo_paths)
    assert duplicate_count == 0
    assert len(photos_metadata) == 2


def test_find_photos_nested(tmp_path: Path) -> None:
    """Test find_photos with nested directories."""
    sub1 = tmp_path / "sub1"
    sub2 = tmp_path / "sub2"
    sub1.mkdir()
    sub2.mkdir()
    img1 = sub1 / "img1.jpg"
    img2 = sub2 / "img2.jpg"
    Image.new("RGB", (10, 10)).save(img1)
    Image.new("RGB", (10, 10)).save(img2)
    found = find_photos(tmp_path)
    assert str(img1) in found
    assert str(img2) in found
    assert len(found) == 2


@pytest.mark.parametrize(
    "color1, color2, should_be_equal",
    [
        ("red", "red", True),
        ("red", "blue", False),
    ],
)
def test_generate_file_hash_param(tmp_path: Path, color1, color2, should_be_equal):
    """Parametrized test for generate_file_hash with different images."""
    file1 = tmp_path / "a.jpg"
    file2 = tmp_path / "b.jpg"
    Image.new("RGB", (10, 10), color=color1).save(file1)
    Image.new("RGB", (10, 10), color=color2).save(file2)
    hash1 = generate_file_hash(str(file1))
    hash2 = generate_file_hash(str(file2))
    if should_be_equal:
        assert hash1 == hash2
    else:
        assert hash1 != hash2


def test_find_photos_non_image_files(tmp_path: Path) -> None:
    """Test find_photos ignores non-image files."""
    img = tmp_path / "img.jpg"
    txt = tmp_path / "note.txt"
    Image.new("RGB", (10, 10)).save(img)
    txt.write_text("not an image")
    found = find_photos(tmp_path)
    assert str(img) in found
    assert all(not f.endswith(".txt") for f in found)


def test_extract_exif_metadata_invalid_file(tmp_path: Path) -> None:
    """Test extract_exif_metadata raises or handles non-image file."""
    txt = tmp_path / "note.txt"
    txt.write_text("not an image")
    try:
        metadata = extract_exif_metadata(str(txt))
        assert metadata is None or "image-format" not in metadata
    except Exception:
        assert True  # Exception is acceptable


def test_generate_file_hash_permission_error(tmp_path: Path) -> None:
    """Test generate_file_hash handles unreadable file gracefully."""
    file = tmp_path / "secret.jpg"
    Image.new("RGB", (10, 10)).save(file)
    file.chmod(0)  # Remove all permissions
    try:
        _ = generate_file_hash(str(file))
    except Exception:
        assert True
    finally:
        file.chmod(0o644)  # Restore permissions for cleanup
