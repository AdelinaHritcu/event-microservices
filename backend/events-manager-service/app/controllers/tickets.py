from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, JSONResponse

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

BASE = "/api/event-manager/tickets"


def raise_for(code: int, res) -> None:
    """Translate a (status, payload) service result into an HTTPException."""
    if code in (200, 201, 204):
        return
    detail = res.get("detail", res) if isinstance(res, dict) else (res or "Error")
    raise HTTPException(status_code=code, detail=detail)


def paged_links(base: str, page: int, per_page: int, total: int, parent: str, extra_q: str = "") -> Dict[str, dict]:
    # plain dicts: every DTO module declares its own Link model
    links: Dict[str, dict] = {
        "self": {"href": f"{base}?page={page}&items_per_page={per_page}{extra_q}", "type": "GET"},
        "parent": {"href": parent, "type": "GET"},
    }
    if page * per_page < total:
        links["next"] = {"href": f"{base}?page={page + 1}&items_per_page={per_page}{extra_q}", "type": "GET"}
    if page > 1:
        links["prev"] = {"href": f"{base}?page={page - 1}&items_per_page={per_page}{extra_q}", "type": "GET"}
    return links


@router.get("", response_model=TicketListResponse)
def list_tickets(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    event_id: Optional[int] = Query(None),
    package_id: Optional[int] = Query(None),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    items, total = TicketsService.list_tickets(
        page=page,
        per_page=items_per_page,
        event_id=event_id,
        package_id=package_id,
        p=p,
    )

    q_ev = "" if event_id is None else f"&event_id={event_id}"
    q_pkg = "" if package_id is None else f"&package_id={package_id}"

    return TicketListResponse(
        items=items,
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links=paged_links(BASE, page, items_per_page, total, "/api/event-manager", q_ev + q_pkg),
    )


@router.put(
    "/{code}",
    response_model=TicketOut,
    responses={201: {"description": "Ticket sold"}, 204: {"description": "Identical ticket already exists"}},
)
def upsert_ticket(
    code: str,
    payload: TicketIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event", "client")),
):
    """
    Sell a ticket with a client-chosen code (used by Client WebService – chain call).
    A `client` may buy for any active event/package; an `owner-event` only for its own.
    """
    if p.role == "owner-event":
        TicketsService.assert_can_manage_ticket_target(
            p, event_id=payload.event_id, package_id=payload.package_id
        )

    code_, res = TicketsService.upsert_ticket(code, payload.event_id, payload.package_id)
    raise_for(code_, res)

    if code_ == 204:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return JSONResponse(status_code=201, content=res.model_dump(by_alias=True))


@router.get("/{code}", response_model=TicketOut)
def get_ticket(
    code: str,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    t = TicketsService.assert_can_access_ticket(code, p)
    return TicketsService.build_ticket_out(t)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TicketOut)
def create_ticket(
    data: TicketIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    TicketsService.assert_can_manage_ticket_target(
        p, event_id=data.event_id, package_id=data.package_id
    )
    code, res = TicketsService.create_ticket(data)
    raise_for(code, res)
    return res


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(
    code: str,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    TicketsService.assert_can_access_ticket(code, p)
    code_, payload = TicketsService.delete_ticket(code)
    raise_for(code_, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
