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
from app.services.tickets_service import TicketsService
from app.security.auth import require_roles, Principal

router = APIRouter(
    prefix="/api/event-manager/tickets",
    tags=["tickets"],
)


@router.get("", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    event_id: Optional[int] = Query(None),
    package_id: Optional[int] = Query(None),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    try:
        items, total = TicketsService.list_tickets(
            page=page,
            per_page=items_per_page,
            event_id=event_id,
            package_id=package_id,
            p=p,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

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


@router.put("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def upsert_ticket(
    code: str,
    payload: TicketIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    if (payload.event_id is None and payload.package_id is None) or (
        payload.event_id is not None and payload.package_id is not None
    ):
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one between event_id and package_id",
        )

    TicketsService.assert_can_manage_ticket_target(
        p, event_id=payload.event_id, package_id=payload.package_id
    )

    try:
        ticket, conflict = TicketsService.create_ticket_if_not_exists(
            code=code,
            event_id=payload.event_id,
            package_id=payload.package_id,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if conflict:
        raise HTTPException(
            status_code=409,
            detail={
                "ticket_code": code,
                "event_id": payload.event_id,
                "package_id": payload.package_id,
            },
        )

    return None


@router.get("/{code}", response_model=TicketOut)
def get_ticket(
    code: str,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    TicketsService.assert_can_access_ticket(code, p)

    try:
        res = TicketsService.get_ticket(code)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return res


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TicketOut)
def create_ticket(
    data: TicketIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    TicketsService.assert_can_manage_ticket_target(
        p, event_id=data.event_id, package_id=data.package_id
    )

    try:
        code, res = TicketsService.create_ticket(data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if code == 404:
        detail = (
            res.get("detail", "Related resource not found.")
            if isinstance(res, dict)
            else "Related resource not found."
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    if code == 409:
        detail = (
            res.get("detail", "Ticket creation conflict.")
            if isinstance(res, dict)
            else "Ticket creation conflict."
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

    return res


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    code: str,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    TicketsService.assert_can_access_ticket(code, p)

    try:
        code_, payload = TicketsService.delete_ticket(code)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if code_ == 404:
        detail = (
            payload.get("detail", "Ticket not found")
            if isinstance(payload, dict)
            else "Ticket not found"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
