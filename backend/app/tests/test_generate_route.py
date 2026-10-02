"""End-to-end pin: generate route, board, and store read-back see one sequence."""

import pytest
from fastapi.testclient import TestClient

from app.db import connect
from app.main import app
from app.seed import init_db
from app.services.rota_store import read_week_slots


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    init_db()
    return TestClient(app)


def test_generate_board_and_store_readback_are_pinned(client):
    r = client.post("/api/weeks/1/generate", json={})
    assert r.status_code == 200

    c = connect()
    stored = read_week_slots(c, 1)
    c.close()
    assert len(stored) == 21  # 7 days x 3 seeded clean tasks

    # The generate response is the store read-back, not a parallel computation.
    assert r.json()["slots"] == stored
    assert r.json()["count"] == len(stored)

    board = client.get("/api/weeks/1/board").json()
    board_slots = [{"day": a["day"], "task_id": a["task_id"], "member_id": a["member_id"]}
                   for a in board["assignments"]]
    assert board_slots == stored


def test_generate_unknown_week_404(client):
    assert client.post("/api/weeks/999/generate", json={}).status_code == 404
