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
    color: str


class HeatmapSummaryOut(BaseModel):
    hottest_slot: str | None
    avg_online: float
    peak_online: int


class HeatmapDayDetailOut(BaseModel):
    name: str
    duration_minutes: int


class HeatmapOut(BaseModel):
    month: str
    available_months: list[str]
    bucket: str
    generated_at: str
    cells: list[HeatmapCellOut]
    day_details: dict[str, list[HeatmapDayDetailOut]]
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
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    bucket: str = Query(default="day", pattern="^day$"),
):
    return get_heatmap(month=month, bucket=bucket)
