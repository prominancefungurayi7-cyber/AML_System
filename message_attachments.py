"""Private, bounded evidence uploads and a versioned message content envelope.

The database keeps its existing message schema.  Only authenticated application
routes may resolve these private files; no user supplied path is ever stored.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from urllib.parse import unquote, urlsplit
import uuid
import warnings
import zipfile
from xml.etree import ElementTree

from PIL import Image
from werkzeug.utils import secure_filename


MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_ARCHIVE_BYTES = 50 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 1000
MAX_CAPTION_LENGTH = 10_000
PREFIX = "__AML_ATTACHMENT_V1__:"
SUPPORTED_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp",
                                  ".pdf", ".txt", ".csv", ".docx", ".xlsx", ".pptx"})
_IMAGE_TYPES = {".png": ("PNG", "image/png"), ".jpg": ("JPEG", "image/jpeg"),
                ".jpeg": ("JPEG", "image/jpeg"), ".gif": ("GIF", "image/gif"),
                ".webp": ("WEBP", "image/webp")}
_OFFICE_TYPES = {
    ".docx": ("word/document.xml", "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
              "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    ".xlsx": ("xl/workbook.xml", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ".pptx": ("ppt/presentation.xml", "application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
              "application/vnd.openxmlformats-officedocument.presentationml.presentation"),
}
_MEDIA_TYPES = frozenset({value[1] for value in _IMAGE_TYPES.values()} |
                         {value[2] for value in _OFFICE_TYPES.values()} |
                         {"application/pdf", "text/plain", "text/csv"})
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"[0-9a-f]{32}\Z")
_METADATA_KEYS = frozenset({"id", "name", "size", "media_type", "sha256"})


class AttachmentError(ValueError):
    """An upload or stored attachment envelope is invalid."""


def _identifier(value):
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise AttachmentError("Invalid attachment identifier.")
    parsed = uuid.UUID(hex=value)
    if parsed.version != 4 or parsed.variant != uuid.RFC_4122:
        raise AttachmentError("Invalid attachment identifier.")
    return value


def attachment_path(root, attachment_id):
    """Resolve a UUID file within the application's private upload directory."""
    attachment_id = _identifier(attachment_id)
    directory = Path(root).resolve()
    # Resolve the trusted root, never the UUID leaf: resolving a leaf symlink
    # could make removal delete another stored attachment instead of the link.
    path = directory / attachment_id
    if path.is_symlink():
        raise AttachmentError("Invalid attachment path.")
    return path


def _filename(value):
    if not isinstance(value, str):
        raise AttachmentError("Choose a file with a supported filename.")
    # A basename is a label only; storage always uses a server UUID.
    label = secure_filename(value.replace("\\", "/").rsplit("/", 1)[-1])
    suffix = Path(label).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise AttachmentError("Supported files: PNG, JPEG, GIF, WebP, PDF, TXT, CSV, DOCX, XLSX and PPTX.")
    stem = Path(label).stem.strip("._") or "document"
    return stem[:160] + suffix


def _xml(raw):
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper or b"\x00" in raw:
        raise AttachmentError("Office files with unsafe XML are not supported.")
    try:
        return ElementTree.fromstring(raw)
    except ElementTree.ParseError as exc:
        raise AttachmentError("The Office file contains invalid XML.") from exc


def _safe_external_hyperlink(relation):
    """Permit ordinary references, excluding externally loaded Office parts."""
    target = relation.attrib.get("Target", "")
    if (relation.attrib.get("TargetMode", "").strip().lower() != "external" or
            not relation.attrib.get("Type", "").endswith("/hyperlink") or
            "\\" in target or any(ord(char) < 32 or ord(char) == 127
                                    for char in unquote(target))):
        return False
    try:
        parsed = urlsplit(target.strip())
        if parsed.scheme.lower() in {"http", "https"}:
            return bool(parsed.hostname)
        if parsed.scheme.lower() == "mailto":
            return bool(parsed.path) and not parsed.netloc
    except ValueError:
        return False
    return False


def _validate_office(content, suffix):
    expected_path, expected_content_type, media_type = _OFFICE_TYPES[suffix]
    if not content.startswith(b"PK\x03\x04"):
        raise AttachmentError("The file content does not match its Office extension.")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > MAX_ARCHIVE_ENTRIES:
                raise AttachmentError("The Office file contains too many archive entries.")
            names = set()
            total_size = 0
            documents = {}
            allowed_parts = {".xml", ".rels", ".png", ".jpg", ".jpeg", ".gif", ".webp",
                             ".bmp", ".tif", ".tiff", ".emf", ".wmf", ".odttf"}
            for entry in entries:
                name = entry.filename
                parts = PurePosixPath(name).parts
                if (not name or name.startswith("/") or "\\" in name or ":" in name or
                        ".." in parts or name in names or
                        stat.S_ISLNK(entry.external_attr >> 16)):
                    raise AttachmentError("The Office file contains an unsafe archive path.")
                names.add(name)
                if entry.flag_bits & 1:
                    raise AttachmentError("Encrypted Office files are not supported.")
                total_size += entry.file_size
                if (entry.file_size < 0 or total_size > MAX_ARCHIVE_BYTES or
                        entry.file_size > max(entry.compress_size, 1) * 100):
                    raise AttachmentError("The Office file exceeds safe archive limits.")
                if entry.is_dir():
                    continue
                if (PurePosixPath(name).suffix.lower() not in allowed_parts or
                        "vbaproject" in name.lower() or "/embeddings/" in name.lower()):
                    raise AttachmentError("Office macros and embedded active files are not supported.")
                raw = archive.read(entry)
                if name.endswith((".xml", ".rels")):
                    document = _xml(raw)
                    documents[name] = document
                    if name.endswith(".rels"):
                        for relation in document.iter():
                            target = relation.attrib.get("Target", "").strip()
                            if ((relation.attrib.get("TargetMode", "").strip().lower() == "external" or
                                    ":" in target or target.startswith(("//", "\\"))) and
                                    not _safe_external_hyperlink(relation)):
                                raise AttachmentError("Externally loaded Office content is not supported.")
            if expected_path not in documents or "[Content_Types].xml" not in documents:
                raise AttachmentError("The file content does not match its Office extension.")
            matching = False
            for node in documents["[Content_Types].xml"].iter():
                part_type = node.attrib.get("ContentType", "")
                if "macroenabled" in part_type.lower() or "vbaproject" in part_type.lower():
                    raise AttachmentError("Office macros are not supported.")
                if (node.attrib.get("PartName") == "/" + expected_path and
                        part_type == expected_content_type):
                    matching = True
            if not matching:
                raise AttachmentError("The file content does not match its Office extension.")
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, EOFError) as exc:
        raise AttachmentError("The Office file is damaged or unsupported.") from exc
    return media_type


def _media_type(content, suffix):
    if suffix in _IMAGE_TYPES:
        expected, media_type = _IMAGE_TYPES[suffix]
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as image:
                    if image.format != expected:
                        raise AttachmentError("The image content does not match its filename.")
                    if image.width < 1 or image.height < 1 or image.width * image.height > MAX_IMAGE_PIXELS:
                        raise AttachmentError("Images must contain no more than 20 million pixels.")
                    if getattr(image, "n_frames", 1) > 500:
                        raise AttachmentError("The image contains too many animation frames.")
                    if image.width * image.height * getattr(image, "n_frames", 1) > 100_000_000:
                        raise AttachmentError("The image animation exceeds safe image limits.")
                    image.verify()
        except AttachmentError:
            raise
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombWarning,
                Image.DecompressionBombError) as exc:
            raise AttachmentError("The image is invalid or exceeds safe image limits.") from exc
        return media_type
    if suffix in _OFFICE_TYPES:
        return _validate_office(content, suffix)
    if suffix == ".pdf":
        if not re.match(rb"%PDF-(?:1\.[0-9]|2\.0)(?:\r|\n)", content) or b"%%EOF" not in content[-1024:]:
            raise AttachmentError("The file content does not match a complete PDF document.")
        return "application/pdf"
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise AttachmentError("TXT and CSV files must contain UTF-8 text.") from exc
    if any(ord(char) < 32 and char not in "\t\r\n" for char in text):
        raise AttachmentError("The file contains binary data rather than plain text.")
    if re.search(r"<(?:!doctype\s+html|html|svg|script)(?:\s|>)", text, re.IGNORECASE):
        raise AttachmentError("HTML, SVG and script files are not supported.")
    return "text/csv" if suffix == ".csv" else "text/plain"


def save_upload(file_storage, root, attachment_id):
    """Validate one bounded upload and create an immutable private UUID file."""
    path = attachment_path(root, attachment_id)
    name = _filename(getattr(file_storage, "filename", None))
    try:
        content = file_storage.read(MAX_FILE_SIZE + 1)
    except (OSError, ValueError) as exc:
        raise AttachmentError("The uploaded file could not be read.") from exc
    if not isinstance(content, bytes) or not content:
        raise AttachmentError("Choose a non-empty file.")
    if len(content) > MAX_FILE_SIZE:
        raise AttachmentError("Each attachment must be 10 MB or smaller.")
    media_type = _media_type(content, Path(name).suffix)
    metadata = {"id": attachment_id, "name": name, "size": len(content),
                "media_type": media_type, "sha256": hashlib.sha256(content).hexdigest()}
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(content)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return metadata


def remove_upload(root, attachment_id):
    attachment_path(root, attachment_id).unlink(missing_ok=True)


def _validated_metadata(metadata):
    if not isinstance(metadata, dict) or set(metadata) not in (_METADATA_KEYS, _METADATA_KEYS | {"request_id"}):
        raise AttachmentError("Invalid attachment metadata.")
    _identifier(metadata["id"])
    if "request_id" in metadata:
        _identifier(metadata["request_id"])
    if not isinstance(metadata["name"], str) or _filename(metadata["name"]) != metadata["name"]:
        raise AttachmentError("Invalid attachment filename.")
    if type(metadata["size"]) is not int or not 1 <= metadata["size"] <= MAX_FILE_SIZE:
        raise AttachmentError("Invalid attachment size.")
    if not isinstance(metadata["media_type"], str) or metadata["media_type"] not in _MEDIA_TYPES:
        raise AttachmentError("Invalid attachment media type.")
    suffix = Path(metadata["name"]).suffix
    expected_media = (_IMAGE_TYPES[suffix][1] if suffix in _IMAGE_TYPES else
                      _OFFICE_TYPES[suffix][2] if suffix in _OFFICE_TYPES else
                      {".pdf": "application/pdf", ".txt": "text/plain", ".csv": "text/csv"}[suffix])
    if metadata["media_type"] != expected_media:
        raise AttachmentError("Attachment media type does not match its filename.")
    if not isinstance(metadata["sha256"], str) or not _HASH.fullmatch(metadata["sha256"]):
        raise AttachmentError("Invalid attachment checksum.")
    return dict(metadata)


def encode_message(caption, metadata):
    if not isinstance(caption, str) or len(caption) > MAX_CAPTION_LENGTH or caption.startswith(PREFIX):
        raise AttachmentError("Invalid attachment caption.")
    payload = {"attachment": _validated_metadata(metadata), "caption": caption}
    return PREFIX + json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)


def decode_message(content):
    if not isinstance(content, str):
        raise AttachmentError("Invalid message content.")
    if not content.startswith(PREFIX):
        return content, None
    if len(content) > MAX_CAPTION_LENGTH * 12 + 2048:
        raise AttachmentError("Invalid attachment envelope.")
    try:
        payload = json.loads(content[len(PREFIX):])
    except (json.JSONDecodeError, RecursionError) as exc:
        raise AttachmentError("Invalid attachment envelope.") from exc
    if not isinstance(payload, dict) or set(payload) != {"caption", "attachment"}:
        raise AttachmentError("Invalid attachment envelope.")
    caption = payload["caption"]
    metadata = payload["attachment"]
    # Require the exact canonical encoding, rejecting duplicate JSON keys and
    # alternate ambiguous encodings as well as malformed or unsafe metadata.
    if encode_message(caption, metadata) != content:
        raise AttachmentError("Invalid attachment envelope.")
    return caption, dict(metadata)
