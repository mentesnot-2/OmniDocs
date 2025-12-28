import io

from api.models import IngestionJob


def test_ingestion_job_status_endpoint(client, make_user, monkeypatch):
    from tests.conftest import DummyEmbeeddingGenerator

    user = make_user()
    client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )

    monkeypatch.setattr(
        "api.services.ingestion_jobs.get_embedding_generator",
        lambda: DummyEmbeeddingGenerator(),
    )

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
