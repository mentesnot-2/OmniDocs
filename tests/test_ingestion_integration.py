import io
import os
from pathlib import Path

import pytest

from tests.conftest import DummyEmbeeddingGenerator, DummyRetriever


def test_upload_indexes_retrievable_chunks(client, make_user, monkeypatch, tmp_path):
    monkeypatch.setenv("VECTOR_STORE_PATH", str(tmp_path / "chroma"))
    monkeypatch.setattr(
        "api.services.ingestion_jobs.get_embedding_generator",
        lambda: DummyEmbeeddingGenerator(),
    )
    monkeypatch.setattr(
        "api.services.runtime_services.get_retriever",
        lambda: DummyRetriever(),
    )

    user = make_user()
    client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )

    content = b"OmniDocs integration test document about quarterly revenue growth."
    upload = client.post(
        "/documents/upload",
        files={"file": ("integration.txt", io.BytesIO(content), "text/plain")},
    )
    assert upload.status_code == 200

    query = client.post(
        "/documents/query",
        json={"question": "What does the document mention?"},
    )
    assert query.status_code == 200
    body = query.json()
    assert "answer" in body


def test_small_pdf_passes_validation():
    from api.services.file_validation import validate_uploaded_file_content

    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<<>>endobj\n"
        b"xref\n0 1\n0000000000 65535 f \n"
        b"trailer<<>>\nstartxref\n0\n%%EOF"
    )
    validate_uploaded_file_content("sample.pdf", pdf_bytes)
