from fastapi import APIRouter
from pydantic import BaseModel

from ..data import enter_dc, leave_dc, get_people

router = APIRouter()

class NameIn(BaseModel):
    name: str

class PersonOut(BaseModel):
    name: str
    entered_at: str

@router.get("/get-people", response_model=list[PersonOut])
def api_get_people():
    return get_people()

@router.post("/enter")
def api_enter_dc(body: NameIn):
    enter_dc(body.name)
    return {"ok": True}

@router.post("/leave")
def api_leave_dc(body: NameIn):
    leave_dc(body.name)
    return {"ok": True}
