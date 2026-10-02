"""Orchestrator tests: pure computation only — SQLite must not be touched in-process."""

import ast
import sqlite3
from pathlib import Path

import pytest

from app.services import rota_planner
from app.services.rota_planner import plan_week_slots


@pytest.fixture(autouse=True)
def no_sqlite_in_process(monkeypatch):
    """Any sqlite3.connect attempt during an orchestrator test fails the test."""
    def boom(*args, **kwargs):
        raise AssertionError("orchestrator must not connect to SQLite")
    monkeypatch.setattr(sqlite3, "connect", boom)


def test_plan_covers_grid_round_robin():
    slots = plan_week_slots([1, 2, 3], [10, 20], days=7)
    assert len(slots) == 14
    assert slots[0] == {"day": 0, "task_id": 10, "member_id": 1}
    assert slots[1]["member_id"] == 2
    assert slots[3]["member_id"] == 1  # wraps


def test_plan_respects_task_input_order():
    slots = plan_week_slots([1], [20, 10], days=1)
    assert [s["task_id"] for s in slots] == [20, 10]


def test_plan_empty_inputs():
    assert plan_week_slots([], [10], days=7) == []
    assert plan_week_slots([1], [], days=7) == []


def test_planner_module_carries_no_db_access():
    """The orchestrator must not import a DB module or call connection/execute APIs."""
    tree = ast.parse(Path(rota_planner.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not [m for m in imported if "sqlite" in m or m == "app.db" or m.endswith(".db")]
    called = {n.func.id for n in ast.walk(tree)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    assert not (called & {"connect", "execute", "executemany", "executescript"})
