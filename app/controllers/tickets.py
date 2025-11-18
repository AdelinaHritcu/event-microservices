from fastapi import APIRouter, Depends, HTTPException, Query
from app.controllers.deps import get_db
from app.dtos.schemas import TicketIn
from app.services import tickets_service

router = APIRouter(prefix="/api/event-manager/tickets", tags=["tickets"])

@router.get("")
def list_tickets(
    page: int = Query(0, ge=0),
    items_per_page: int = Query(10, ge=1, le=100),
    event_id: int | None = Query(None),
    package_id: int | None = Query(None),
    db=Depends(get_db),
):
    return tickets_service.list_tickets(
        page=page,
        per_page=items_per_page,
        event_id=event_id,
        package_id=package_id,
    )

@router.get("/{code}")
def get_ticket(code: str, db=Depends(get_db)):
    res = tickets_service.get_ticket(code)
    if not res:
        raise HTTPException(404, "Ticket not found")
    return res

@router.post("", status_code=201)
def create_ticket(data: TicketIn, db=Depends(get_db)):
    code, res = tickets_service.create_ticket(data)
    if code == 404:
        raise HTTPException(404, "Event not found")
    if code == 409:
        raise HTTPException(409, "No more seats available for event")
    return res

@router.delete("/{code}", status_code=204)
def delete_ticket(code: str, db=Depends(get_db)):
    code_ = tickets_service.delete_ticket(code)
    if code_ == 404:
        raise HTTPException(404, "Ticket not found")
