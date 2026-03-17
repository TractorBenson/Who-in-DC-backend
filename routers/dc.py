from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from service import enter_dc, get_heatmap, get_leaderboard, get_people, leave_dc

router = APIRouter()


class NameIn(BaseModel):
    name: str = Field(min_length=1)


class PersonOut(BaseModel):
    name: str
    entered_at: str


class LeaderboardItemOut(BaseModel):
    rank: int
    name: str
    duration_minutes: int
    diff_from_prev_minutes: int


class LeaderboardOut(BaseModel):
    range: str
    generated_at: str
    items: list[LeaderboardItemOut]


class HeatmapCellOut(BaseModel):
    date: str
    hour: int
    value: float


class HeatmapSummaryOut(BaseModel):
    hottest_slot: str | None
    avg_online: float
    peak_online: int


class HeatmapOut(BaseModel):
    range: str
    bucket: str
    generated_at: str
    cells: list[HeatmapCellOut]
    summary: HeatmapSummaryOut


@router.get("/get-people", response_model=list[PersonOut])
def api_get_people():
    return get_people()


@router.post("/enter")
def api_enter_dc(body: NameIn):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name cannot be empty")
    enter_dc(name)
    return {"ok": True, "message": f"Welcome to DC, {name}!"}


@router.post("/leave")
def api_leave_dc(body: NameIn):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="name cannot be empty")
    leave_dc(name)
    return {"ok": True, "message": f"Goodbye from DC, {name}!"}


@router.get("/leaderboard", response_model=LeaderboardOut)
def api_leaderboard(
    range: str = Query(default="today", pattern="^(today|week|month)$"),
    limit: int = Query(default=50, ge=1, le=200),
):
    return get_leaderboard(range_name=range, limit=limit)


@router.get("/heatmap", response_model=HeatmapOut)
def api_heatmap(
    range: str = Query(default="7d", pattern="^(7d|30d)$"),
    bucket: str = Query(default="hour", pattern="^hour$"),
):
    return get_heatmap(range_name=range, bucket=bucket)
