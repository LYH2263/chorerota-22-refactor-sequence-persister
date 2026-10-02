"""Persister tests: writable and readable; read-back must equal planner output."""

import sqlite3

import pytest

from app.services.rota_planner import plan_week_slots
from app.services.rota_store import (
    load_assignment_inputs,
    read_week_slots,
    save_week_slots,
)

SCHEMA = """
CREATE TABLE members(id INTEGER PRIMARY KEY, name TEXT, active INT, data_quality TEXT);
CREATE TABLE tasks(id INTEGER PRIMARY KEY, title TEXT, weight INT, data_quality TEXT);
CREATE TABLE weeks(id INTEGER PRIMARY KEY, label TEXT, status TEXT);
CREATE TABLE assignments(id INTEGER PRIMARY KEY AUTOINCREMENT, week_id INT, day INT, task_id INT, member_id INT);
"""


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    c.execute("INSERT INTO weeks(label,status) VALUES ('w1','draft')")
    yield c
    c.close()


def test_readback_equals_planner_output(conn):
    slots = plan_week_slots([1, 2, 3], [10, 20], days=7)
    save_week_slots(conn, 1, slots)
    assert read_week_slots(conn, 1) == slots


def test_readback_preserves_task_input_order(conn):
    slots = plan_week_slots([1, 2], [20, 10], days=3)
    save_week_slots(conn, 1, slots)
    assert read_week_slots(conn, 1) == slots


def test_save_replaces_previous_grid(conn):
    save_week_slots(conn, 1, plan_week_slots([1, 2], [10], days=7))
    shorter = plan_week_slots([1], [10], days=2)
    save_week_slots(conn, 1, shorter)
    assert read_week_slots(conn, 1) == shorter


def test_save_marks_week_ready(conn):
    save_week_slots(conn, 1, plan_week_slots([1], [10], days=1))
    status = conn.execute("SELECT status FROM weeks WHERE id=1").fetchone()["status"]
    assert status == "ready"


def test_load_assignment_inputs_filters_dirty(conn):
    conn.execute("INSERT INTO members(name,active,data_quality) VALUES "
                 "('a',1,'clean'),('b',0,'clean'),('c',1,'dirty')")
    conn.execute("INSERT INTO tasks(title,weight,data_quality) VALUES "
                 "('t1',1,'clean'),('t2',0,'clean'),('t3',2,'dirty')")
    mids, tids = load_assignment_inputs(conn)
    assert mids == [1]
    assert tids == [1]
