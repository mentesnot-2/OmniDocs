import io

from api.models import IngestionJob


def test_ingestion_job_status_endpoint(client, make_user, monkeypatch):
    from tests.conftest import DummyEmbeeddingGenerator

    user = make_user()
    client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )

    def run_job_sync(job_id):
        monkeypatch.setattr(
            "api.services.ingestion_jobs.get_embedding_generator",
            lambda: DummyEmbeeddingGenerator(),
        )
        from api.services.ingestion_jobs import process_ingestion_job

        process_ingestion_job(job_id)

    monkeypatch.setattr("api.routes.documents.process_ingestion_job", run_job_sync)

    upload = client.post(
        "/documents/upload",
        files={"file": ("job.txt", io.BytesIO(b"Job status polling test content."), "text/plain")},
    )
    assert upload.status_code == 200
    job_id = upload.json()["job_id"]

    status = client.get(f"/documents/jobs/{job_id}")
    assert status.status_code == 200
    body = status.json()
    assert body["id"] == job_id
    assert body["status"] in {"completed", "queued", "processing"}
