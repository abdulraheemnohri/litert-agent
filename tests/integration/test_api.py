"""Integration tests for the FastAPI API."""

import pytest
from fastapi.testclient import TestClient

from litert_agent.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_status(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    assert res.json()["model_provider"] if "model_provider" in res.json() else True
    assert res.json()["agent"]


def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert "healthy" in res.json()
    assert isinstance(res.json()["healthy"], bool)


def test_tasks_roundtrip(client):
    res = client.post("/api/tasks", json={"goal": "test goal"})
    assert res.status_code == 200
    task_id = res.json()["id"]
    res = client.get("/api/tasks")
    assert any(t["id"] == task_id for t in res.json()["tasks"])


def test_skills(client):
    res = client.get("/api/skills")
    assert res.status_code == 200
    assert len(res.json()["skills"]) >= 10


def test_page_render(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "LiteRT Agent" in res.text
