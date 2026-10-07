"""Tests for chat/agent web pages and chat API."""

import pytest
from fastapi.testclient import TestClient

from litert_agent.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_chat_page_renders(client):
    res = client.get("/chat")
    assert res.status_code == 200


def test_agent_page_renders(client):
    res = client.get("/agent")
    assert res.status_code == 200


def test_status_shape(client):
    res = client.get("/api/status")
    assert res.status_code == 200
    assert "model_provider" in res.json()
