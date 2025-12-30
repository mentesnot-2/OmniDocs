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

    def run_job_sync(job_id):
        monkeypatch.setattr(
            "api.services.ingestion_jobs.get_embedding_generator",
            lambda: DummyEmbeeddingGenerator(),
        )
        from api.services.ingestion_jobs import process_ingestion_job

        process_ingestion_job(job_id)

    monkeypatch.setattr("api.routes.documents.process_ingestion_job", run_job_sync)

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
    assert len(versions.json()["versions"]) >= 1

    document = db_session.query(Document).filter(Document.user_id == user.id).one()
    assert document.filename == "notes.txt"
    version = db_session.query(DocumentVersion).filter(DocumentVersion.document_id == document.id).one()
    assert version.version_number == 1
