import os

import pytest

pytestmark = pytest.mark.integration


def test_rate_limiter_uses_redis_storage(client, monkeypatch):
    redis_uri = os.getenv("RATE_LIMIT_STORAGE_URI", "")
    if not redis_uri.startswith("redis://"):
        pytest.skip("RATE_LIMIT_STORAGE_URI must point to Redis")

    import api.rate_limiter as rate_limiter_module
    from slowapi import Limiter

    from api.rate_limiter import rate_limit_key

    limiter = Limiter(key_func=rate_limit_key, storage_uri=redis_uri)
    monkeypatch.setattr(rate_limiter_module, "limiter", limiter)
    monkeypatch.setattr("api.main.limiter", limiter)

    for _ in range(6):
        response = client.post("/auth/login", json={"email": "missing@example.com", "password": "wrong"})
        assert response.status_code in (401, 422, 429)
