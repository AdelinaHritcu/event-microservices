from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.controllers.deps import get_db
from app.dtos.schemas import EventIn
from app.services import events_service

router = APIRouter(prefix="/api/event-manager/events", tags=["events"])

@router.get("")
def list_events(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db=Depends(get_db),
):
    rows, total = events_service.list_events(
        page=page, per_page=items_per_page, name=name, location=location
    )
    offset = (page - 1) * items_per_page
    has_next = offset + items_per_page < total
    q_name = "" if not name else f"&name={name}"
    q_loc = "" if not location else f"&location={location}"
    base = "/api/event-manager/events"
    self_href = f"{base}?page={page}&items_per_page={items_per_page}{q_name}{q_loc}"
    next_href = (
        f"{base}?page={page+1}&items_per_page={items_per_page}{q_name}{q_loc}"
        if has_next else None
    )
    prev_href = (
        f"{base}?page={page-1}&items_per_page={items_per_page}{q_name}{q_loc}"
        if page > 1 else None
    )
    return {
        "page": page,
        "items_per_page": items_per_page,
        "total_items": total,
        "events": rows,
        "_links": {
            "self": {"href": self_href},
            "next": {"href": next_href} if next_href else None,
            "prev": {"href": prev_href} if prev_href else None,
            "parent": {"href": "/api/event-manager"},
        },
    }

@router.get("/{event_id}")
def get_event(event_id: int, db=Depends(get_db)):
    res = events_service.get_event(event_id)
    if not res:
        raise HTTPException(404, "Event not found")
    res.setdefault("_links", {})
    res["_links"].update({
        "self": {"href": f"/api/event-manager/events/{event_id}"},
        "parent": {"href": "/api/event-manager/events"},
    })
    return res

@router.post("", status_code=201)
def create_event(data: EventIn, db=Depends(get_db)):
    created = events_service.create_event(data)
    event_id = created.get("id")
    created.setdefault("_links", {})
    created["_links"].update({
        "self": {"href": f"/api/event-manager/events/{event_id}"} if event_id is not None else None,
        "parent": {"href": "/api/event-manager/events"},
    })
    return created

@router.put("/{event_id}")
def update_event(event_id: int, data: EventIn, db=Depends(get_db)):
    code, res = events_service.update_event(event_id, data)
    if code == 404:
        raise HTTPException(404, "Event not found")
    if code == 409:
        raise HTTPException(409, "Edit locked: tickets already sold")
    res.setdefault("_links", {})
    res["_links"].update({
        "self": {"href": f"/api/event-manager/events/{event_id}"},
        "parent": {"href": "/api/event-manager/events"},
    })
    return res

@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, db=Depends(get_db)):
    code = events_service.delete_event(event_id)
    if code == 404:
        raise HTTPException(404, "Event not found")
    if code == 409:
        raise HTTPException(409, "Delete blocked: tickets already sold")
