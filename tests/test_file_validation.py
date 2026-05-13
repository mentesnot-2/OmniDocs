import io
import zipfile

import pytest
from fastapi import HTTPException

from api.services.file_validation import validate_uploaded_file_content



def test_rejects_binary_renamed_as_pdf():
    with pytest.raises(HTTPException) as exc:
        validate_uploaded_file_content("report.pdf", b"MZ fake executable bytes")
    assert exc.value.status_code == 400


def test_accepts_simple_text_file():
    validate_uploaded_file_content("notes.txt", b"Hello, world!")


def test_rejects_binary_payload_for_text_extension():
    with pytest.raises(HTTPException) as exc:
        validate_uploaded_file_content("notes.txt", b"\x00\x01\x02\x03")

    assert exc.value.status_code == 400


def test_rejects_invalid_docx_structure():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("random.txt", "not a real docx")
    with pytest.raises(HTTPException) as exc:
        validate_uploaded_file_content("file.docx", buf.getvalue())
    assert exc.value.status_code == 400

def test_accepts_minimal_docx_like_archive(monkeypatch):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("word/document.xml", "<document></document>")
    
    monkeypatch.setattr(
        "api.services.file_validation._detect_mime",
        lambda content: "application/zip",
    )
    validate_uploaded_file_content("file.docx", buf.getvalue())
