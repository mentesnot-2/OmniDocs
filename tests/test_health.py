def test_health_liveness(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_returns_checks(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert "checks" in body
    assert body["checks"]["database"] == "ok"
    assert body["checks"]["storage"] == "ok"
