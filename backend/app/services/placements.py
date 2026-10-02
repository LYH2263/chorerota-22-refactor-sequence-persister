"""落格器：把编排器算出的格序列写入 assignments，并可按写入顺序读回。

是唯一对 assignments 做整周重写的写库边界；事务提交由调用方
（HTTP 路由）负责，本模块只在传入的连接上执行。
"""


def write_week_slots(conn, week_id: int, slots: list[dict]) -> None:
    """Replace the week's grid with `slots` and mark the week ready."""
    conn.execute("DELETE FROM assignments WHERE week_id=?", (week_id,))
    conn.executemany(
        "INSERT INTO assignments(week_id,day,task_id,member_id) VALUES (?,?,?,?)",
        [(week_id, s["day"], s["task_id"], s["member_id"]) for s in slots],
    )
    conn.execute("UPDATE weeks SET status='ready' WHERE id=?", (week_id,))


def read_week_slots(conn, week_id: int) -> list[dict]:
    """Read the week's grid back as a slot sequence, in insertion order.

    assignments.id is AUTOINCREMENT, so ORDER BY id replays exactly the
    sequence write_week_slots inserted — comparable to the planner output.
    """
    rows = conn.execute(
        "SELECT day,task_id,member_id FROM assignments WHERE week_id=? ORDER BY id",
        (week_id,),
    ).fetchall()
    return [{"day": r["day"], "task_id": r["task_id"], "member_id": r["member_id"]} for r in rows]
