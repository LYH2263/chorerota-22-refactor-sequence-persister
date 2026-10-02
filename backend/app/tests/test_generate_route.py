"""生成路由测例：生成后看板与落格读回同钉；路由体内禁止 for 循环插入格位。

直接调用路由函数（FastAPI 装饰器返回原函数），不引入 httpx。
"""
import ast
import inspect

import pytest

from app import main, seed
from app.db import connect
from app.services.planner import plan_week_slots
from app.services.placements import read_week_slots


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    seed.init_db()
    conn = connect()
    yield conn
    conn.close()


def _grid(rows):
    key = lambda a: (a["day"], a["task_id"], a["member_id"])
    return sorted(({"day": a["day"], "task_id": a["task_id"], "member_id": a["member_id"]} for a in rows),
                  key=key)


def test_generate_pins_board_to_readback(db):
    resp = main.generate(1, main.GenBody())
    assert resp["count"] == len(resp["slots"]) > 0

    board = main.week_board(1)
    back = read_week_slots(db, 1)
    # 看板与落格读回同钉：同一周格，同一内容
    assert _grid(board["assignments"]) == _grid(back)
    # 且与编排器对同输入（路由同口径筛选）的输出一致
    mids = [r["id"] for r in db.execute(
        "SELECT id FROM members WHERE active=1 AND data_quality='clean' ORDER BY id")]
    tids = [r["id"] for r in db.execute(
        "SELECT id FROM tasks WHERE data_quality='clean' AND weight>0 ORDER BY id")]
    assert back == plan_week_slots(mids, tids, days=7)
    assert resp["count"] == len(back)


def test_generate_unknown_week_404(db):
    with pytest.raises(main.HTTPException) as e:
        main.generate(999, main.GenBody())
    assert e.value.status_code == 404


def test_generate_route_body_has_no_slot_insert_loop():
    # 路由函数体内禁止 for/while 循环插入格位（INSERT INTO assignments）
    src = inspect.getsource(main.generate)
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            texts = [c.value.upper().replace(" ", "") for c in ast.walk(node)
                     if isinstance(c, ast.Constant) and isinstance(c.value, str)]
            assert not any("INSERTINTOASSIGNMENTS" in t for t in texts)
