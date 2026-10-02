"""编排器 orchestrator: compute the next week's slot sequence. Pure — no DB, no SQL.

Shares the pure grid math with the persister via app.engines.rota so the
planned sequence and the stored sequence can never drift apart. This module
must never gain INSERT/UPDATE statements or a sqlite import; swap-confirm
writes stay in the route service (app.main).
"""

from app.engines.rota import build_week_slots


def plan_week_slots(member_ids: list[int], task_ids: list[int], days: int = 7) -> list[dict]:
    """Ordered slot sequence for one week: [{day, task_id, member_id}, ...].

    Order is day-major, tasks in the given input order; the store preserves
    this exact order on write and read-back.
    """
    return build_week_slots(list(member_ids), list(task_ids), days=days)
