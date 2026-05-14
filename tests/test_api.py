import sys
from pathlib import Path

import httpx
import pytest

root_path = Path(__file__).resolve().parents[1]
sys.path.append(str(root_path))

from app.main import app


@pytest.fixture
def client():
    transport = httpx.ASGITransport(app=app)
    client = httpx.AsyncClient(transport=transport, base_url="http://testserver")
    yield client
    import asyncio

    asyncio.run(client.aclose())


def test_root(client):
    import asyncio

    response = asyncio.run(client.get("/"))
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Questions API funcionando"
    assert "/questions" in data["endpoints"]


def test_list_questions(client):
    import asyncio

    response = asyncio.run(client.get("/questions?limit=2"))
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 2


def test_search_questions(client):
    import asyncio

    response = asyncio.run(
        client.get("/questions/search", params={"query": "capital"})
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("capital" in q["question"].lower() for q in data)


def test_create_question(client):
    import asyncio

    payload = {
        "question": "¿Qué herramienta usamos para crear APIs en Python?",
        "answer": "FastAPI",
        "category": "Programación",
        "source": "test",
    }
    response = asyncio.run(client.post("/questions", json=payload))
    assert response.status_code == 201
    data = response.json()
    assert data["question"] == payload["question"]
    assert data["answer"] == payload["answer"]
    assert data["category"] == payload["category"]
    assert data["source"] == payload["source"]
    assert isinstance(data["id"], int)


def test_stats(client):
    import asyncio

    response = asyncio.run(client.get("/stats"))
    assert response.status_code == 200
    data = response.json()
    assert "total_questions" in data
    assert "questions_by_category" in data
    assert isinstance(data["total_questions"], int)
    assert isinstance(data["questions_by_category"], dict)
