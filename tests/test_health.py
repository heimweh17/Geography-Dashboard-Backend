from fastapi.testclient import TestClient

from app.main import create_app


def test_liveness_and_readiness_are_available():
    with TestClient(create_app()) as client:
        liveness = client.get("/healthz")
        readiness = client.get("/readyz")

    assert liveness.status_code == 200
    assert readiness.status_code == 200
    assert liveness.json()["status"] == "ok"
    assert readiness.json()["status"] == "ready"


def test_request_id_is_returned_and_metrics_are_exposed():
    with TestClient(create_app()) as client:
        response = client.get("/healthz", headers={"X-Request-ID": "test-request-id"})
        metrics = client.get("/metrics")

    assert response.headers["X-Request-ID"] == "test-request-id"
    assert metrics.status_code == 200
    assert "geodashboard_http_requests_total" in metrics.text
