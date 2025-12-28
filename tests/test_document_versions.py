import io

from api.models import Document, DocumentVersion


def _login(client, user):
    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )
    assert response.status_code == 200
    return response


def test_upload_registers_document_version(client, db_session, make_user, monkeypatch):
    from tests.conftest import DummyEmbeeddingGenerator

    user = make_user()
    monkeypatch.setattr(
        "api.services.ingestion_jobs.get_embedding_generator",
        lambda: DummyEmbeeddingGenerator(),
    )

    _login(client, user)
    content = b"Sample document text for versioning test.\n"
    response = client.post(
        "/documents/upload",
        files={"file": ("notes.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"]
    assert payload["version"] == 1

    versions = client.get("/documents/notes.txt/versions")
    assert versions.status_code == 200
    body = versions.json()["versions"]
    assert len(body) >= 1
    assert body[0]["storage_key"]

    document = db_session.query(Document).filter(Document.user_id == user.id).one()
    version = db_session.query(DocumentVersion).filter(DocumentVersion.document_id == document.id).one()
    assert version.version_number == 1
    assert version.storage_key == body[0]["storage_key"]


def test_reupload_creates_second_version_with_distinct_storage_key(client, db_session, make_user, monkeypatch):
    from tests.conftest import DummyEmbeeddingGenerator

    user = make_user()
    monkeypatch.setattr(
        "api.services.ingestion_jobs.get_embedding_generator",
        lambda: DummyEmbeeddingGenerator(),
    )
    _login(client, user)

    for content in (b"first version", b"second version"):
        client.post(
            "/documents/upload",
            files={"file": ("notes.txt", io.BytesIO(content), "text/plain")},
        )

    versions = client.get("/documents/notes.txt/versions").json()["versions"]
    assert len(versions) == 2
    keys = {v["storage_key"] for v in versions}
    assert len(keys) == 2
    numbers = {v["version"] for v in versions}
    assert numbers == {1, 2}
