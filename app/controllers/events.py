from fastapi import APIRouter, Depends, HTTPException, Query
from app.controllers.deps import get_db  # doar ca side-effect de conexiune
from app.dtos.schemas import EventIn
from app.services import events_service

router = APIRouter(prefix="/api/event-manager/events", tags=["events"])

@router.get("")
def list_events(page:int=Query(0, ge=0), items_per_page:int=Query(10, ge=1, le=100),
                name:str|None=None, location:str|None=None, db=Depends(get_db)):
    return events_service.list_events(page=page, per_page=items_per_page, name=name, location=location)

@router.get("/{event_id}")
def get_event(event_id:int, db=Depends(get_db)):
    res = events_service.get_event(event_id)
    if not res: raise HTTPException(404, "Event not found")
    return res

@router.post("", status_code=201)
def create_event(data:EventIn, db=Depends(get_db)):
    return events_service.create_event(data)

@router.put("/{event_id}")
def update_event(event_id:int, data:EventIn, db=Depends(get_db)):
    code, res = events_service.update_event(event_id, data)
    if code == 404: raise HTTPException(404, "Event not found")
    if code == 409: raise HTTPException(409, "Edit locked: tickets already sold")
    return res

@router.delete("/{event_id}", status_code=204)
def delete_event(event_id:int, db=Depends(get_db)):
    code = events_service.delete_event(event_id)
    if code == 404: raise HTTPException(404, "Event not found")
    if code == 409: raise HTTPException(409, "Delete blocked: tickets already sold")
