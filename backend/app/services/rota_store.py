"""落格器 persister: own every SQL statement about the assignments grid.

Writes a planned slot sequence into `assignments` and reads it back in the
same order, so callers can pin the stored week to the planner's output.
"""


def get_week(conn, week_id: int):
    """Fetch one week row, or None."""
    return conn.execute("SELECT * FROM weeks WHERE id=?", (week_id,)).fetchone()


def load_assignment_inputs(conn) -> tuple[list[int], list[int]]:
    """Eligible (member_ids, task_ids) for planning, both ordered by id."""
    mids = [r["id"] for r in conn.execute(
        "SELECT id FROM members WHERE active=1 AND data_quality='clean' ORDER BY id")]
    tids = [r["id"] for r in conn.execute(
        "SELECT id FROM tasks WHERE data_quality='clean' AND weight>0 ORDER BY id")]
    return mids, tids


def save_week_slots(conn, week_id: int, slots: list[dict]) -> None:
    """Replace a week's assignments with the planned sequence and mark it ready."""
    conn.execute("DELETE FROM assignments WHERE week_id=?", (week_id,))
    conn.executemany(
        "INSERT INTO assignments(week_id,day,task_id,member_id) VALUES (?,?,?,?)",
        [(week_id, s["day"], s["task_id"], s["member_id"]) for s in slots],
    )
    conn.execute("UPDATE weeks SET status='ready' WHERE id=?", (week_id,))
    conn.commit()


def read_week_slots(conn, week_id: int) -> list[dict]:
    """Read back the stored sequence in insertion (rowid) order.

    Returns the same shape and order the planner produced:
    [{day, task_id, member_id}, ...].
    """
    rows = conn.execute(
        "SELECT day,task_id,member_id FROM assignments WHERE week_id=? ORDER BY id",
        (week_id,),
    )
    return [{"day": day, "task_id": task_id, "member_id": member_id}
            for day, task_id, member_id in rows]
