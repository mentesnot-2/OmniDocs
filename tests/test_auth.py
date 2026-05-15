from datetime import datetime

import pytest

from api.core.security import decode_refresh_token
from api.models import RefreshSession, User


def test_login_sets_auth_cookies_for_active_user(client, db_session, make_user):
    user = make_user()

    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )

    assert response.status_code == 200
    assert response.cookies.get("omnidocs_token")
    assert response.cookies.get("omnidocs_refresh")

    sessions = db_session.query(RefreshSession).filter(RefreshSession.user_id == user.id).all()
    assert len(sessions) == 1
    assert sessions[0].revoked_at is None


def test_login_blocks_inactive_user(client, make_user):
    user = make_user(is_active=False)

    response = client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Your account is not active. Please contact support."


def test_refresh_rotates_valid_refresh_session(client, db_session, make_user):
    user = make_user()

    login_response = client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )
    old_refresh = login_response.cookies.get("omnidocs_refresh")
    old_payload = decode_refresh_token(old_refresh)

    refresh_response = client.post(
        "/auth/refresh",
        cookies={"omnidocs_refresh": old_refresh},
    )

    assert refresh_response.status_code == 200
    new_refresh = refresh_response.cookies.get("omnidocs_refresh")
    assert new_refresh
    assert new_refresh != old_refresh

    db_session.expire_all()
    old_session = db_session.query(RefreshSession).filter(RefreshSession.jti == old_payload["jti"]).one()
    new_payload = decode_refresh_token(new_refresh)
    new_session = db_session.query(RefreshSession).filter(RefreshSession.jti == new_payload["jti"]).one()

    assert old_session.revoked_at is not None
    assert old_session.replaced_by_jti == new_payload["jti"]
    assert new_session.revoked_at is None


@pytest.mark.parametrize("mode", ["revoked", "missing"])
def test_refresh_fails_for_revoked_or_missing_session(client, db_session, make_user, mode):
    user = make_user()

    login_response = client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )
    refresh_token = login_response.cookies.get("omnidocs_refresh")
    payload = decode_refresh_token(refresh_token)
    session = db_session.query(RefreshSession).filter(RefreshSession.jti == payload["jti"]).one()

    if mode == "revoked":
        session.revoked_at = datetime.utcnow()
        db_session.commit()
    else:
        db_session.delete(session)
        db_session.commit()

    response = client.post(
        "/auth/refresh",
        cookies={"omnidocs_refresh": refresh_token},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired refresh token"


def test_logout_revokes_refresh_session_and_clears_cookie(client, db_session, make_user):
    user = make_user()

    login_response = client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )
    refresh_token = login_response.cookies.get("omnidocs_refresh")
    payload = decode_refresh_token(refresh_token)

    logout_response = client.post(
        "/auth/logout",
        cookies={"omnidocs_refresh": refresh_token},
    )

    assert logout_response.status_code == 200
    db_session.expire_all()
    session = db_session.query(RefreshSession).filter(RefreshSession.jti == payload["jti"]).one()
    assert session.revoked_at is not None

    refresh_response = client.post(
        "/auth/refresh",
        cookies={"omnidocs_refresh": refresh_token},
    )
    assert refresh_response.status_code == 401


def test_google_oauth_callback_blocks_unsafe_email_auto_link(client, db_session, make_user, monkeypatch):
    existing_user = make_user(email="existing@example.com")

    import api.routes.auth as auth_routes

    monkeypatch.setattr(auth_routes, "SSO_ENABLED", True)
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_ID", "google-client-id")
    monkeypatch.setattr(auth_routes, "GOOGLE_CLIENT_SECRET", "google-client-secret")

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload

        def json(self):
            return self._payload

    class FakeAsyncClient:
        def __init__(self,*args,**kwargs):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse(200, {"access_token": "google-token"})

        async def get(self, *args, **kwargs):
            return FakeResponse(
                200,
                {
                    "email": existing_user.email,
                    "sub": "google-oauth-sub",
                    "email_verified": True,
                },
            )

    monkeypatch.setattr(auth_routes.httpx, "AsyncClient", FakeAsyncClient)

    client.cookies.set(auth_routes.OAUTH_STATE_COOKIE, "state-123")
    response = client.get(
        "/auth/oauth/google/callback",
        params={"code": "auth-code", "state": "state-123"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "/login?error=" in response.headers["location"]

    db_session.expire_all()
    same_user = db_session.get(User, existing_user.id)
    assert same_user.oauth_sub is None


def test_refresh_token_reuse_revokes_descendant_chain(client, db_session, make_user):
    user = make_user()

    login_response = client.post(
        "/auth/login",
        json={"email": user.email, "password": user._raw_password},
    )

    refresh_token_1 = login_response.cookies.get("omnidocs_refresh")
    payload_1 = decode_refresh_token(refresh_token_1)

    refresh_response = client.post(
        "/auth/refresh",
        cookies={"omnidocs_refresh": refresh_token_1},
    )

    assert refresh_response.status_code == 200

    refresh_token_2 = refresh_response.cookies.get("omnidocs_refresh")
    payload_2 = decode_refresh_token(refresh_token_2)


    # Replay the old revoked token

    replay_response = client.post(
        "/auth/refresh",
        cookies={"omnidocs_refresh": refresh_token_1},
    )

    assert replay_response.status_code == 401

    db_session.expire_all()

    old_session = db_session.query(RefreshSession).filter(RefreshSession.jti == payload_1["jti"]).one()
    new_session = db_session.query(RefreshSession).filter(RefreshSession.jti == payload_2["jti"]).one()

    assert old_session.revoked_at is not None
    assert new_session.revoked_at is not None


    # The rotated token should no longer work after reuse detection
    response_after_reuse = client.post(
        "/auth/refresh",
        cookies={"omnidocs_refresh": refresh_token_2},
    )
    assert response_after_reuse.status_code == 401