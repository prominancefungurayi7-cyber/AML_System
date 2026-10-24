"""Validated, metadata-free profile photos in private application storage.

Only a positive database user identifier determines a stored filename. Routes
must authenticate and authorize access before using these storage helpers.
"""
from __future__ import annotations

import hashlib
import io
import os
from pathlib import Path
import uuid
import warnings

from PIL import Image, ImageOps


MAX_PHOTO_SIZE = 5 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
PHOTO_DIMENSIONS = (512, 512)
_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}


class ProfilePhotoError(ValueError):
    """A profile photo or its storage path is invalid."""


def photo_path(root, user_id):
    """Return the private JPEG path, rejecting untrusted IDs and leaf links."""
    if type(user_id) is not int or not 0 < user_id <= 2**63 - 1:
        raise ProfilePhotoError("Invalid profile user identifier.")
    # The configured directory and its parent belong to the application owner.
    # Resolve that trusted root, never a potentially linked leaf.
    path = Path(root).resolve() / f"user-{user_id}.jpg"
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ProfilePhotoError("Invalid profile photo path.")
    return path


def photo_version(root, user_id):
    """Return the stored JPEG checksum for cache invalidation, if present."""
    path = photo_path(root, user_id)
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ProfilePhotoError("The profile photo could not be read.") from exc


def _normalized_jpeg(file_storage):
    filename = getattr(file_storage, "filename", None)
    if not isinstance(filename, str):
        raise ProfilePhotoError("Choose a PNG, JPEG or WebP photo.")
    suffix = Path(filename.replace("\\", "/").rsplit("/", 1)[-1]).suffix.lower()
    expected_format = _FORMATS.get(suffix)
    if expected_format is None:
        raise ProfilePhotoError("Choose a PNG, JPEG or WebP photo.")
    try:
        content = file_storage.read(MAX_PHOTO_SIZE + 1)
    except (OSError, ValueError) as exc:
        raise ProfilePhotoError("The uploaded photo could not be read.") from exc
    if not isinstance(content, bytes) or not content:
        raise ProfilePhotoError("Choose a non-empty photo.")
    if len(content) > MAX_PHOTO_SIZE:
        raise ProfilePhotoError("Profile photos must be 5 MB or smaller.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format != expected_format:
                    raise ProfilePhotoError("The photo content does not match its filename.")
                if (image.width < 1 or image.height < 1 or
                        image.width * image.height > MAX_IMAGE_PIXELS):
                    raise ProfilePhotoError("Photos must contain no more than 20 million pixels.")
                if getattr(image, "n_frames", 1) != 1:
                    raise ProfilePhotoError("Animated profile photos are not supported.")
                image.verify()
            # Verification invalidates the decoder; reopen and fully decode
            # before accepting, then apply orientation before the centre crop.
            with Image.open(io.BytesIO(content)) as image:
                image.load()
                oriented = ImageOps.exif_transpose(image)
                rgba = oriented.convert("RGBA")
                flattened = Image.new("RGB", rgba.size, (245, 246, 248))
                flattened.paste(rgba, mask=rgba.getchannel("A"))
                fitted = ImageOps.fit(flattened, PHOTO_DIMENSIONS, Image.Resampling.LANCZOS)
                # A fresh canvas carries no EXIF, ICC profile, comments, names
                # or other uploaded metadata into the normalized JPEG.
                clean = Image.new("RGB", PHOTO_DIMENSIONS)
                clean.paste(fitted)
                encoded = io.BytesIO()
                clean.save(encoded, "JPEG", quality=88)
                return encoded.getvalue()
    except ProfilePhotoError:
        raise
    except (OSError, ValueError, SyntaxError, Image.DecompressionBombWarning,
            Image.DecompressionBombError) as exc:
        raise ProfilePhotoError("The photo is invalid or exceeds safe image limits.") from exc


def save_photo(file_storage, root, user_id):
    """Atomically replace a user's photo only after complete validation."""
    path = photo_path(root, user_id)
    content = _normalized_jpeg(file_storage)
    temporary = path.parent / (".profile-" + uuid.uuid4().hex + ".tmp")
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        # A rejected linked leaf must never be replaced or followed, including
        # when it appeared while the new image was being prepared.
        photo_path(root, user_id)
        os.replace(temporary, path)
    except (OSError, ValueError) as exc:
        if isinstance(exc, ProfilePhotoError):
            raise
        raise ProfilePhotoError("The profile photo could not be saved.") from exc
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            # Storage permission failures must not replace the useful upload
            # error with a second exception from best-effort cleanup.
            pass
    return hashlib.sha256(content).hexdigest()


def remove_photo(root, user_id):
    """Remove only this user's stored photo; repeated removal is harmless."""
    try:
        photo_path(root, user_id).unlink(missing_ok=True)
    except ProfilePhotoError:
        raise
    except OSError as exc:
        raise ProfilePhotoError("The profile photo could not be removed.") from exc
