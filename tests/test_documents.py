import io

from api.models import Document


def test_delete_document_removes_registry(client, db_session, make_user, monkeypatch):
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
        files={"file": ("remove-me.txt", io.BytesIO(b"delete me"), "text/plain")},
    )
    assert upload.status_code == 200

    deleted = client.delete("/documents/remove-me.txt")
    assert deleted.status_code == 200

    remaining = db_session.query(Document).filter(Document.user_id == user.id).count()
    assert remaining == 0
