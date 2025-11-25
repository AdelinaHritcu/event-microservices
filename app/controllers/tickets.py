from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response

from app.controllers.deps import get_db
from app.dtos.tickets_schemas import (
    TicketIn,
    TicketOut,
    TicketListResponse,
    Link,
)
from app.services import tickets_service

router = APIRouter(prefix="/api/event-manager/tickets", tags=["tickets"])


@router.get("", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    event_id: Optional[int] = Query(None),
    package_id: Optional[int] = Query(None),
    db=Depends(get_db),
):
    items, total = tickets_service.list_tickets(
        page=page,
        per_page=items_per_page,
        event_id=event_id,
        package_id=package_id,
    )

    base = "/api/event-manager/tickets"
    q_ev = "" if event_id is None else f"&event_id={event_id}"
    q_pkg = "" if package_id is None else f"&package_id={package_id}"

    self_href = f"{base}?page={page}&items_per_page={items_per_page}{q_ev}{q_pkg}"

    links: Dict[str, Link] = {
        "self": Link(href=self_href, type="GET"),
        "parent": Link(href="/api/event-manager", type="GET"),
    }

    return TicketListResponse(
        items=items,
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links=links,
    )


@router.get("/{code}", response_model=TicketOut)
def get_ticket(code: str, db=Depends(get_db)):
    res = tickets_service.get_ticket(code)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return res


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TicketOut)
def create_ticket(data: TicketIn, db=Depends(get_db)):
    code, res = tickets_service.create_ticket(data)

    if code == 404:
        detail = res.get("detail", "Related resource not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    if code == 409:
        detail = res.get("detail", "Ticket creation conflict.")
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    return res


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(code: str, db=Depends(get_db)):
    code_, payload = tickets_service.delete_ticket(code)

    if code_ == 404:
        detail = payload.get("detail", "Ticket not found") if payload else "Ticket not found"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
