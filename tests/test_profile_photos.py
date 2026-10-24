"""Profile photos are validated and normalized using disposable storage only."""
import hashlib
import io
from pathlib import Path
import threading

from PIL import Image
import pytest
from werkzeug.datastructures import FileStorage

import profile_photos as photos


def upload(content, filename="portrait.png"):
    return FileStorage(stream=io.BytesIO(content), filename=filename,
                       content_type="application/octet-stream")


def image_bytes(kind="PNG", color="red", size=(64, 48), **options):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, kind, **options)
    return buffer.getvalue()


@pytest.mark.parametrize("kind,extension", [("PNG", "png"), ("JPEG", "jpg"),
                                            ("JPEG", "jpeg"), ("WEBP", "webp")])
def test_supported_images_become_private_jpegs_with_versions(tmp_path, kind, extension):
    root = tmp_path / "private"
    version = photos.save_photo(upload(image_bytes(kind), f"../portrait.{extension}"), root, 7)
    path = photos.photo_path(root, 7)
    assert path.name == "user-7.jpg"
    assert list(root.iterdir()) == [path]
    assert version == photos.photo_version(root, 7) == hashlib.sha256(path.read_bytes()).hexdigest()
    with Image.open(path) as result:
        assert result.format == "JPEG"
        assert result.size == (512, 512)
        assert result.mode == "RGB"
        assert not result.getexif()
        assert "icc_profile" not in result.info and "comment" not in result.info
    photos.remove_photo(root, 7)
    photos.remove_photo(root, 7)
    assert photos.photo_version(root, 7) is None


@pytest.mark.parametrize("user_id", [True, False, None, 0, -1, 1.0, "1", "../escape", 2**63])
def test_only_positive_database_integer_identifiers_are_allowed(tmp_path, user_id):
    with pytest.raises(photos.ProfilePhotoError, match="identifier"):
        photos.photo_path(tmp_path, user_id)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("content,filename", [
    (b"", "portrait.png"), (b"not an image", "portrait.png"),
    (image_bytes(), "portrait.jpg"), (image_bytes(), "portrait.svg"),
    (image_bytes(), "portrait.gif"), (image_bytes(), "portrait"),
    (image_bytes(), "portrait.png.exe"), (image_bytes(), None),
    (image_bytes()[:40], "portrait.png"),
])
def test_invalid_upload_preserves_previous_photo(tmp_path, content, filename):
    photos.save_photo(upload(image_bytes()), tmp_path, 1)
    previous = photos.photo_path(tmp_path, 1).read_bytes()
    with pytest.raises(photos.ProfilePhotoError):
        photos.save_photo(upload(content, filename), tmp_path, 1)
    assert photos.photo_path(tmp_path, 1).read_bytes() == previous
    assert len(list(tmp_path.iterdir())) == 1


def test_input_size_and_pixel_limits_are_enforced_before_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(photos, "MAX_PHOTO_SIZE", 8)
    with pytest.raises(photos.ProfilePhotoError, match="5 MB"):
        photos.save_photo(upload(b"123456789"), tmp_path, 1)
    monkeypatch.setattr(photos, "MAX_PHOTO_SIZE", 5 * 1024 * 1024)
    monkeypatch.setattr(photos, "MAX_IMAGE_PIXELS", 50)
    with pytest.raises(photos.ProfilePhotoError, match="20 million"):
        photos.save_photo(upload(image_bytes()), tmp_path, 1)
    assert not list(tmp_path.iterdir())


def test_animated_png_is_rejected(tmp_path):
    stream = io.BytesIO()
    first = Image.new("RGB", (16, 16), "red")
    first.save(stream, "PNG", save_all=True,
               append_images=[Image.new("RGB", (16, 16), "blue")], duration=100, loop=0)
    with pytest.raises(photos.ProfilePhotoError, match="Animated"):
        photos.save_photo(upload(stream.getvalue()), tmp_path, 1)
    assert not list(tmp_path.iterdir())


def test_transparency_is_flattened_onto_neutral_background(tmp_path):
    stream = io.BytesIO()
    Image.new("RGBA", (16, 16), (255, 0, 0, 0)).save(stream, "PNG")
    photos.save_photo(upload(stream.getvalue()), tmp_path, 1)
    with Image.open(photos.photo_path(tmp_path, 1)) as result:
        assert all(abs(actual - expected) <= 2 for actual, expected in
                   zip(result.getpixel((256, 256)), (245, 246, 248)))


def test_exif_orientation_is_applied_and_private_metadata_removed(tmp_path):
    # Orientation 6 rotates this left-red/right-blue image into top-red/bottom-blue.
    original = Image.new("RGB", (80, 80), "blue")
    original.paste("red", (0, 0, 40, 80))
    exif = Image.Exif()
    exif[274] = 6
    exif[270] = "private description"
    exif[315] = "private name"
    stream = io.BytesIO()
    original.save(stream, "JPEG", exif=exif, comment=b"private comment")
    photos.save_photo(upload(stream.getvalue(), "portrait.jpeg"), tmp_path, 1)
    content = photos.photo_path(tmp_path, 1).read_bytes()
    assert b"private" not in content
    with Image.open(io.BytesIO(content)) as result:
        top, bottom = result.getpixel((256, 100)), result.getpixel((256, 400))
        assert top[0] > 230 and top[2] < 25
        assert bottom[2] > 230 and bottom[0] < 25
        assert not result.getexif()


def test_write_failure_preserves_previous_photo_and_cleans_temporary(tmp_path, monkeypatch):
    previous_version = photos.save_photo(upload(image_bytes()), tmp_path, 1)
    def rejected_replace(*args):
        raise PermissionError("simulated storage failure")
    monkeypatch.setattr(photos.os, "replace", rejected_replace)
    with pytest.raises(photos.ProfilePhotoError, match="could not be saved"):
        photos.save_photo(upload(image_bytes(color="blue")), tmp_path, 1)
    assert photos.photo_version(tmp_path, 1) == previous_version
    assert list(tmp_path.iterdir()) == [photos.photo_path(tmp_path, 1)]


def test_incomplete_write_is_never_published_and_is_cleaned_up(tmp_path, monkeypatch):
    previous_version = photos.save_photo(upload(image_bytes()), tmp_path, 1)
    def rejected_flush(*args):
        raise OSError("simulated disk flush failure")
    monkeypatch.setattr(photos.os, "fsync", rejected_flush)
    with pytest.raises(photos.ProfilePhotoError, match="could not be saved"):
        photos.save_photo(upload(image_bytes(color="blue")), tmp_path, 1)
    assert photos.photo_version(tmp_path, 1) == previous_version
    assert list(tmp_path.iterdir()) == [photos.photo_path(tmp_path, 1)]


def test_misconfigured_storage_reports_controlled_error(tmp_path):
    root = tmp_path / "not-a-directory"
    root.write_bytes(b"preserve")
    with pytest.raises(photos.ProfilePhotoError, match="could not be saved"):
        photos.save_photo(upload(image_bytes()), root, 1)
    assert root.read_bytes() == b"preserve"


def test_linked_leaf_is_rejected_without_reading_or_removing_target(tmp_path, monkeypatch):
    target = tmp_path / "target.jpg"
    target.write_bytes(b"do not change")
    alias = tmp_path / "user-1.jpg"
    try:
        alias.symlink_to(target)
    except OSError:
        original = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda path: path == alias or original(path))
    for operation in (lambda: photos.photo_version(tmp_path, 1),
                      lambda: photos.remove_photo(tmp_path, 1),
                      lambda: photos.save_photo(upload(image_bytes()), tmp_path, 1)):
        with pytest.raises(photos.ProfilePhotoError, match="path"):
            operation()
    assert target.read_bytes() == b"do not change"


def test_atomic_replacement_keeps_reader_on_complete_old_or_new_photo(tmp_path, monkeypatch):
    photos.save_photo(upload(image_bytes()), tmp_path, 1)
    path = photos.photo_path(tmp_path, 1)
    previous = path.read_bytes()
    original_replace = photos.os.replace
    reached_replace, continue_replace = threading.Event(), threading.Event()
    failures = []
    def paused_replace(source, destination):
        reached_replace.set()
        assert continue_replace.wait(10)
        original_replace(source, destination)
    monkeypatch.setattr(photos.os, "replace", paused_replace)
    def writer():
        try:
            photos.save_photo(upload(image_bytes(color="blue")), tmp_path, 1)
        except Exception as exc:
            failures.append(exc)
    thread = threading.Thread(target=writer)
    thread.start()
    try:
        assert reached_replace.wait(10)
        assert path.read_bytes() == previous
    finally:
        continue_replace.set()
        thread.join(10)
    assert not thread.is_alive() and not failures
    assert path.read_bytes() != previous
    with Image.open(path) as result:
        result.load()
        assert result.size == (512, 512)
    assert list(tmp_path.iterdir()) == [path]
