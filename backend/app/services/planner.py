"""编排器：只计算下一周格序列，不触碰数据库。

输入是路由已筛选好的成员/任务 id 列表，输出是格位序列
（[{"day", "task_id", "member_id"}...]，按 day→task 顺序）。
写库由落格器 app.services.placements 负责；本模块不得引入任何
sqlite/db 依赖，测例在进程内不连接 SQLite。
"""

from app.engines.rota import build_week_slots


def plan_week_slots(member_ids: list[int], task_ids: list[int], days: int = 7) -> list[dict]:
    """Compute the next week's grid for the given rosters. Pure: no I/O.

    Shares the round-robin pure function with the engine so the planned
    sequence is exactly what the persister later writes and reads back.
    """
    return build_week_slots(list(member_ids), list(task_ids), days=days)
