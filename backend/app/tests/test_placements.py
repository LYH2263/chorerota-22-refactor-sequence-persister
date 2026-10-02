"""落格器测例：可写可读 SQLite；读回序列必须等于编排器对同输入的输出。"""
import pytest

from app import seed
from app.db import connect
from app.services.planner import plan_week_slots
from app.services.placements import read_week_slots, write_week_slots


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    seed.init_db()
    conn = connect()
    yield conn
    conn.close()


def test_readback_equals_planner_output(db):
    slots = plan_week_slots([1, 2, 3], [1, 2], days=7)
    write_week_slots(db, 1, slots)
    assert read_week_slots(db, 1) == slots


def test_readback_matches_planner_for_other_inputs(db):
    for mids, tids, days in [([7], [9, 8, 5], 3), ([4, 2], [6], 10)]:
        slots = plan_week_slots(mids, tids, days=days)
        write_week_slots(db, 1, slots)
        assert read_week_slots(db, 1) == slots


def test_rewrite_replaces_grid(db):
    write_week_slots(db, 1, plan_week_slots([1, 2], [1], days=7))
    slots = plan_week_slots([9], [2, 3], days=2)
    write_week_slots(db, 1, slots)
    assert read_week_slots(db, 1) == slots  # 旧格位被清掉，只剩新序列


def test_write_marks_week_ready(db):
    write_week_slots(db, 1, plan_week_slots([1], [1], days=1))
    status = db.execute("SELECT status FROM weeks WHERE id=1").fetchone()["status"]
    assert status == "ready"


def test_write_empty_slots_clears_week(db):
    write_week_slots(db, 1, plan_week_slots([1, 2], [1], days=7))
    write_week_slots(db, 1, plan_week_slots([], [], days=7))
    assert read_week_slots(db, 1) == []
