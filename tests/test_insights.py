import json
from unittest.mock import Mock

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app
from app.services import ai_gemini


def test_embedded_insight_auth_failure_recovery_and_quota(monkeypatch):
    client = TestClient(create_app())
    payload = {"analysis_result": {"summary": {"total_points": 3}}}
    assert client.post("/ai/insights", json=payload).status_code == 401
    credentials = {"email": "insights@example.com", "password": "test-account-only"}
    assert client.post("/auth/register", json=credentials).status_code == 201
    token = client.post("/auth/login", data={"username": credentials["email"], "password": credentials["password"]}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    def submit():
        return client.post("/ai/insights", json=payload, headers=headers)

    monkeypatch.setattr(settings, "gemini_api_key", None)
    assert submit().status_code == 503
    monkeypatch.setattr(settings, "gemini_api_key", "test-only")
    provider = Mock()
    monkeypatch.setattr(ai_gemini.requests, "post", provider)
    provider.return_value.json.return_value = {"candidates": []}
    assert submit().status_code == 502
    narrative = {"text": "The dataset contains three points.", "method": "Point count", "highlights": ["3 points"]}
    provider.return_value.json.return_value = {"candidates": [{"content": {"parts": [{"text": json.dumps(narrative)}]}}]}
    assert submit().json()["text"] == narrative["text"]
    assert submit().status_code == 429
    assert provider.call_count == 2
