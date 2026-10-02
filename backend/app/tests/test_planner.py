"""编排器测例：纯计算，进程内不得连接 SQLite（本文件不引入 sqlite3/app.db）。"""
import ast
from pathlib import Path

import app.services.planner as planner
from app.engines.rota import build_week_slots
from app.services.planner import plan_week_slots


def test_plan_covers_grid_in_day_task_order():
    slots = plan_week_slots([1, 2, 3], [10, 20], days=7)
    assert len(slots) == 14
    assert [(s["day"], s["task_id"]) for s in slots[:4]] == [
        (0, 10), (0, 20), (1, 10), (1, 20),
    ]
    assert slots[0]["member_id"] == 1
    assert slots[3]["member_id"] == 1  # wraps


def test_plan_empty_roster_gives_empty_grid():
    assert plan_week_slots([], [10], days=7) == []
    assert plan_week_slots([1], [], days=7) == []


def test_plan_shares_engine_pure_function():
    # 编排与落格共用纯函数：同输入必须给出同一对外格位序列
    args = ([3, 1, 2], [20, 10])
    assert plan_week_slots(*args, days=5) == build_week_slots(*args, days=5)


def test_planner_module_imports_no_db():
    # 边界守卫：编排器模块本身不得引入 sqlite3 或 app.db
    tree = ast.parse(Path(planner.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not any("sqlite" in m or m == "app.db" for m in imported)
