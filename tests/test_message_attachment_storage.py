"""Evidence upload limits and envelope integrity use temporary files only."""
import hashlib
import io
import json
from pathlib import Path
import uuid
import zipfile
from xml.etree.ElementTree import Element, tostring

from PIL import Image
import pytest
from werkzeug.datastructures import FileStorage

import message_attachments as attachments


def uploaded(content, name="evidence.txt", mimetype=None):
    return FileStorage(stream=io.BytesIO(content), filename=name, content_type=mimetype)


def image_bytes(kind="PNG", size=(12, 8)):
    stream = io.BytesIO()
    Image.new("RGB", size, "white").save(stream, format=kind)
    return stream.getvalue()


def office_bytes(extra=None, kind="docx"):
    main, content_type, _ = attachments._OFFICE_TYPES["." + kind]
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml",
                         '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                         f'<Override PartName="/{main}" ContentType="{content_type}"/></Types>')
        archive.writestr(main, "<document/>")
        for path, content in (extra or {}).items():
            archive.writestr(path, content)
    return stream.getvalue()


def test_private_storage_uses_uuid_and_preserves_content(tmp_path):
    identifier = uuid.uuid4().hex
    content = image_bytes()
    metadata = attachments.save_upload(uploaded(content, "../my screenshot.png", "text/plain"),
                                       tmp_path / "private", identifier)
    assert metadata == {"id": identifier, "name": "my_screenshot.png", "size": len(content),
                        "media_type": "image/png", "sha256": hashlib.sha256(content).hexdigest()}
    stored = attachments.attachment_path(tmp_path / "private", identifier)
    assert stored.name == identifier
    assert stored.read_bytes() == content
    with pytest.raises(FileExistsError):
        attachments.save_upload(uploaded(b"other"), tmp_path / "private", identifier)
    assert stored.read_bytes() == content
    attachments.remove_upload(tmp_path / "private", identifier)
    attachments.remove_upload(tmp_path / "private", identifier)
    assert not stored.exists()


@pytest.mark.parametrize("identifier", ["../escape", "x" * 32, uuid.uuid1().hex,
                                        uuid.uuid4().hex.upper(), str(uuid.uuid4()), ""])
def test_identifiers_are_strict_v4_uuid_hex(tmp_path, identifier):
    with pytest.raises(attachments.AttachmentError):
        attachments.attachment_path(tmp_path, identifier)
    assert not list(tmp_path.iterdir())


def test_uuid_leaf_symlinks_are_rejected_without_deleting_the_target(tmp_path, monkeypatch):
    identifier, other_identifier = uuid.uuid4().hex, uuid.uuid4().hex
    target = tmp_path / other_identifier
    target.write_bytes(b"preserve other attachment")
    alias = tmp_path / identifier
    # Windows can deny symlink creation without Developer Mode. Simulate the
    # leaf's symlink property in that case while retaining the target check.
    try:
        alias.symlink_to(target)
    except OSError:
        original = Path.is_symlink
        monkeypatch.setattr(Path, "is_symlink", lambda path: path == alias or original(path))
    with pytest.raises(attachments.AttachmentError):
        attachments.remove_upload(tmp_path, identifier)
    assert target.read_bytes() == b"preserve other attachment"


def office_with_relationship(target, kind="hyperlink"):
    root = Element("Relationships")
    relation = Element("Relationship", {"Id": "rId10", "TargetMode": "External",
                                        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/" + kind,
                                        "Target": target})
    root.append(relation)
    return office_bytes({"word/_rels/document.xml.rels": tostring(root)})


@pytest.mark.parametrize("target", ["https://doi.org/10.1000/evidence", "http://example.org/reference",
                                    "mailto:officer@example.org"])
def test_office_ordinary_reference_hyperlinks_are_allowed(tmp_path, target):
    metadata = attachments.save_upload(uploaded(office_with_relationship(target), "references.docx"),
                                       tmp_path, uuid.uuid4().hex)
    assert metadata["name"] == "references.docx"


@pytest.mark.parametrize("target,kind", [
    ("file:///C:/private/secret.txt", "hyperlink"),
    ("\\\\server\\share\\file", "hyperlink"),
    ("//server/share/file", "hyperlink"),
    ("javascript:alert(1)", "hyperlink"),
    ("https://example.org/%0aunsafe", "hyperlink"),
    ("https://example.org/image.png", "image"),
    ("https://example.org/template.dotx", "attachedTemplate"),
])
def test_office_unsafe_links_and_external_content_are_rejected(tmp_path, target, kind):
    with pytest.raises(attachments.AttachmentError):
        attachments.save_upload(uploaded(office_with_relationship(target, kind), "evidence.docx"),
                                tmp_path, uuid.uuid4().hex)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("name,content", [
    ("evidence.svg", b"<svg/>"), ("evidence.html", b"<html/>"),
    ("evidence.exe", b"MZanything"), ("evidence.pdf", b"MZanything"),
    ("evidence.png", b"not an image"), ("evidence.jpg", image_bytes()),
    ("evidence.txt", b"MZ\x00\x01\x02"), ("evidence.txt", b"<html>unsafe</html>"),
    ("evidence.txt", b"\xff\xfehello"), ("evidence.txt", b""),
    ("evidence.docx", b"PK\x03\x04invalid zip"),
    ("evidence.docx", office_bytes(kind="xlsx")),
])
def test_rejected_upload_never_creates_file(tmp_path, name, content):
    root = tmp_path / "private"
    with pytest.raises(attachments.AttachmentError):
        attachments.save_upload(uploaded(content, name), root, uuid.uuid4().hex)
    assert not root.exists()


def test_size_limit_does_not_trust_client_metadata(tmp_path, monkeypatch):
    monkeypatch.setattr(attachments, "MAX_FILE_SIZE", 8)
    with pytest.raises(attachments.AttachmentError, match="20 MB"):
        attachments.save_upload(uploaded(b"123456789"), tmp_path, uuid.uuid4().hex)
    assert not list(tmp_path.iterdir())


def test_dimension_limit_rejects_oversized_images(tmp_path, monkeypatch):
    monkeypatch.setattr(attachments, "MAX_IMAGE_PIXELS", 50)
    with pytest.raises(attachments.AttachmentError, match="20 million"):
        attachments.save_upload(uploaded(image_bytes(), "image.png"), tmp_path, uuid.uuid4().hex)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize("name,content,media", [
    ("evidence.txt", b"Account balance: 12.34", "text/plain"),
    ("evidence.csv", b"account,value\nACC1,12.34\n", "text/csv"),
    ("evidence.pdf", b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n", "application/pdf"),
    ("evidence.png", image_bytes(), "image/png"),
    ("evidence.jpg", image_bytes("JPEG"), "image/jpeg"),
    ("evidence.gif", image_bytes("GIF"), "image/gif"),
    ("evidence.webp", image_bytes("WEBP"), "image/webp"),
    ("evidence.docx", office_bytes(), attachments._OFFICE_TYPES[".docx"][2]),
    ("evidence.xlsx", office_bytes(kind="xlsx"), attachments._OFFICE_TYPES[".xlsx"][2]),
    ("evidence.pptx", office_bytes(kind="pptx"), attachments._OFFICE_TYPES[".pptx"][2]),
])
def test_supported_file_types_are_detected_from_content(tmp_path, name, content, media):
    metadata = attachments.save_upload(uploaded(content, name, "application/octet-stream"),
                                       tmp_path, uuid.uuid4().hex)
    assert metadata["media_type"] == media
    assert metadata["size"] == len(content)


@pytest.mark.parametrize("extra", [
    {"../escape.xml": "<root/>"},
    {"word/vbaProject.bin": "macro"},
    {"word/embeddings/file.xml": "<root/>"},
    {"word/executable.exe": "MZ"},
    {"word/unsafe.xml": '<!DOCTYPE root [<!ENTITY x "unsafe">]><root>&x;</root>'},
    {"word/_rels/document.xml.rels": '<Relationships><Relationship TargetMode="External" '
                                      'Target="https://example.test/file"/></Relationships>'},
    {"word/expanded.xml": "<root>" + "0" * 200_000 + "</root>"},
])
def test_office_active_and_unsafe_archives_are_rejected(tmp_path, extra):
    with pytest.raises(attachments.AttachmentError):
        attachments.save_upload(uploaded(office_bytes(extra), "evidence.docx"), tmp_path,
                                uuid.uuid4().hex)
    assert not list(tmp_path.iterdir())


def metadata():
    return {"id": uuid.uuid4().hex, "name": "evidence.png", "size": 23,
            "media_type": "image/png", "sha256": "a" * 64}


def test_canonical_envelope_roundtrip_and_optional_client_request_identifier():
    meta = metadata()
    meta["request_id"] = uuid.uuid4().hex
    content = attachments.encode_message("Screenshot: balance ✓", meta)
    assert content.startswith(attachments.PREFIX)
    assert attachments.decode_message(content) == ("Screenshot: balance ✓", meta)
    assert attachments.decode_message("Ordinary message") == ("Ordinary message", None)


@pytest.mark.parametrize("key,value", [
    ("id", "../outside"), ("request_id", "invalid"), ("name", "../evidence.png"),
    ("name", "evidence.svg"), ("size", True), ("size", -1), ("size", 20 * 1024 * 1024 + 1),
    ("media_type", "text/html"), ("media_type", "text/plain"), ("media_type", []),
    ("sha256", "invalid"), ("path", "C:/secret"),
])
def test_invalid_metadata_is_rejected(key, value):
    meta = metadata()
    meta[key] = value
    with pytest.raises(attachments.AttachmentError):
        attachments.encode_message("Caption", meta)


def test_reserved_prefix_malformed_payload_and_ambiguous_json_are_rejected():
    meta = metadata()
    with pytest.raises(attachments.AttachmentError):
        attachments.encode_message(attachments.PREFIX + "fake", meta)
    malformed = ["{", "[]", "null", '{"caption":"x","attachment":{}}',
                 json.dumps({"caption": "x", "attachment": meta}),
                 attachments.encode_message("x", meta)[len(attachments.PREFIX):].replace(
                     '"caption":"x"', '"caption":"other","caption":"x"')]
    for payload in malformed:
        with pytest.raises(attachments.AttachmentError):
            attachments.decode_message(attachments.PREFIX + payload)
