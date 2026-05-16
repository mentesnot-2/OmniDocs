"""Email verification token hashing (no plaintext in DB)."""

import pytest

from api.core.security import hash_verification_token
from api.models import User


def test_hash_verification_token_is_sha256_hex_stable():
    digest = hash_verification_token("same-secret")
    assert digest == hash_verification_token("same-secret")
    assert len(digest) == 64
    assert digest != hash_verification_token("different-secret")


def test_signup_stores_digest_verify_accepts_plain(monkeypatch, client, db_session):
    import api.routes.auth as auth_routes

    monkeypatch.setattr(auth_routes, "EMAIL_VERIFICATION_REQUIRED", True)
    monkeypatch.setattr(auth_routes, "send_email", lambda *a, **k: None)
    monkeypatch.setattr(
        User,
        "generate_verification_token",
        staticmethod(lambda: "fixture-plain-verification-token"),
    )

    email = "verify_hash_test@example.com"
    res = client.post(
        "/auth/signup",
        json={"email": email, "password": "Str0ngPass!"},
    )
    assert res.status_code == 201

    user = db_session.query(User).filter(User.email == email).one()
    stored = user.verification_token
    assert stored is not None
    assert stored == hash_verification_token("fixture-plain-verification-token")
    assert stored != "fixture-plain-verification-token"

    verify_res = client.get("/auth/verify/fixture-plain-verification-token")
    assert verify_res.status_code == 200
    db_session.expire_all()
    user = db_session.query(User).filter(User.email == email).one()
    assert user.is_verified is True
    assert user.verification_token is None
