"""HTTP routes for week generation: thin adapter over planner + store.

No slot-insert loops here — orchestration is app.services.rota_planner,
persistence is app.services.rota_store. The response is the store read-back,
so the API, the board, and the assignments table stay pinned to one sequence.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import connect
from app.services.rota_planner import plan_week_slots
from app.services.rota_store import (
    get_week,
    load_assignment_inputs,
    read_week_slots,
    save_week_slots,
)

router = APIRouter()


class GenBody(BaseModel):
    days: int = 7


@router.post("/api/weeks/{week_id}/generate")
def generate(week_id: int, body: GenBody = GenBody()):
    c = connect()
    if get_week(c, week_id) is None:
        c.close()
        raise HTTPException(404, "week not found")
    mids, tids = load_assignment_inputs(c)
    slots = plan_week_slots(mids, tids, days=body.days)
    save_week_slots(c, week_id, slots)
    stored = read_week_slots(c, week_id)
    c.close()
    return {"count": len(stored), "slots": stored}
