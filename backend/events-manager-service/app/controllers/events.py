from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse, Response
from peewee import IntegrityError

from app.controllers.deps import get_db
from app.controllers.packages import build_package_item, require_package_owner
from app.controllers.tickets import raise_for, paged_links
from app.links import client_links
from app.dtos.events_schemas import (
    EventIn,
    EventOut,
    EventItem,
    EventListResponse,
    Link,
)
from app.dtos.packages_schemas import PackageListResponse
from app.dtos.tickets_schemas import TicketListResponse, TicketIn, TicketOut
from app.services import events_service, packages_service
from app.services.tickets_service import TicketsService
from app.security.auth import require_roles, Principal, require_owner

router = APIRouter(
    prefix="/api/event-manager/events",
    tags=["events"],
)

BASE = "/api/event-manager/events"


def _links(d: dict):
    return {k: Link(**v) for k, v in d["_links"].items()}


def to_event_item(d: dict) -> EventItem:
    return EventItem(**{k: v for k, v in d.items() if k != "_links"}, links=_links(d))


def to_event_out(d: dict) -> EventOut:
    return EventOut(**{k: v for k, v in d.items() if k != "_links"}, links=_links(d))


def get_event_or_404(event_id: int) -> dict:
    e = events_service.get_event(event_id)
    if not e:
        raise HTTPException(status_code=404, detail="Event not found")
    return e


def require_event_owner(event_id: int, p: Principal) -> dict:
    e = get_event_or_404(event_id)
    require_owner(str(e["id_owner"]), p)
    return e


# ---------------------------------------------------------------- events

@router.get("", response_model=EventListResponse)
def list_events(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None, description="Partial match on name"),
    location: Optional[str] = Query(None, description="Partial match on location"),
    available_tickets: Optional[int] = Query(None, ge=0, description="Minimum available tickets"),
    id_owner: Optional[int] = Query(None, ge=1, description="Only events created by this owner"),
    db=Depends(get_db),
):
    """Public: guests can browse events (Lab 6)."""
    rows, total = events_service.list_events(
        page=page,
        per_page=items_per_page,
        name=name,
        location=location,
        available_tickets=available_tickets,
        id_owner=id_owner,
    )

    q = ""
    if name:
        q += f"&name={name}"
    if location:
        q += f"&location={location}"
    if available_tickets is not None:
        q += f"&available_tickets={available_tickets}"
    if id_owner is not None:
        q += f"&id_owner={id_owner}"

    return EventListResponse(
        items=[to_event_item(r) for r in rows],
        page=page,
        items_per_page=items_per_page,
        total=total,
        links={**paged_links(BASE, page, items_per_page, total, "/api/event-manager", q), **client_links()},
    )


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int = Path(..., ge=1), db=Depends(get_db)):
    return to_event_out(get_event_or_404(event_id))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventOut)
def create_event(
    data: EventIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    # an owner-event always creates events for itself
    # ID_OWNER is always taken from the JWS (Lab 4 / 3.2.2)
    owner_id = int(p.sub)
    try:
        created = events_service.create_event(data, owner_id)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Event name already exists")
    return to_event_out(created)


@router.put(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={201: {"model": EventOut, "description": "Created at the given id"}, 204: {"description": "Replaced"}},
)
def put_event(
    data: EventIn,
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    """Lab 2: PUT creates the resource (201) or replaces it (204)."""
    owner_id = int(p.sub)
    if events_service.get_event(event_id) is None:
        try:
            created = events_service.create_event(data, owner_id, event_id)
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Event name already exists")
        body = to_event_out(created).model_dump(by_alias=True)
        return JSONResponse(status_code=201, content=body, headers={"Location": f"{BASE}/{event_id}"})

    require_event_owner(event_id, p)

    try:
        code, res = events_service.update_event(event_id, data, owner_id)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Event name already exists")
    raise_for(code, res)
    # Lab 2: PUT that replaces an existing resource -> 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    require_event_owner(event_id, p)

    code = events_service.delete_event(event_id)
    if code == 404:
        raise HTTPException(status_code=404, detail="Event not found")
    if code == 409:
        raise HTTPException(status_code=409, detail="Delete blocked: tickets already sold")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------- event <-> event-packets

@router.get("/{event_id}/event-packets", response_model=PackageListResponse)
def list_event_packets_for_event(
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
):
    get_event_or_404(event_id)
    packages = packages_service.list_packages_for_event(event_id)
    items = [
        build_package_item(pck, packages_service.compute_available_tickets(pck))
        for pck in packages
    ]
    return PackageListResponse(
        items=items,
        page=1,
        items_per_page=max(len(items), 1),
        total_items=len(items),
        links={
            "self": {"href": f"{BASE}/{event_id}/event-packets", "type": "GET"},
            "parent": {"href": f"{BASE}/{event_id}", "type": "GET"},
        },
    )


@router.put(
    "/{event_id}/event-packets/{package_id}",
    status_code=status.HTTP_201_CREATED,
    responses={204: {"description": "Already linked"}},
)
def add_event_to_packet(
    event_id: int = Path(..., ge=1),
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    package = require_package_owner(package_id, p)
    code, detail = packages_service.add_event_to_package(package, event_id)
    raise_for(code, detail)
    if code == 204:
        return Response(status_code=204)
    return {
        "event_id": event_id,
        "package_id": package_id,
        "_links": {
            "self": {"href": f"{BASE}/{event_id}/event-packets/{package_id}", "type": "PUT"},
            "parent": {"href": f"{BASE}/{event_id}/event-packets", "type": "GET"},
            "event-packet": {"href": f"/api/event-manager/event-packets/{package_id}", "type": "GET"},
        },
    }


@router.delete("/{event_id}/event-packets/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event_from_packet(
    event_id: int = Path(..., ge=1),
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    package = require_package_owner(package_id, p)
    code, detail = packages_service.remove_event_from_package(package, event_id)
    raise_for(code, detail)
    return Response(status_code=204)


# ------------------------------------------------------------- tickets

@router.get("/{event_id}/tickets", response_model=TicketListResponse)
def list_event_tickets(
    event_id: int = Path(..., ge=1),
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    require_event_owner(event_id, p)
    items, total = TicketsService.list_tickets(
        page=page, per_page=items_per_page, event_id=event_id
    )
    base = f"{BASE}/{event_id}/tickets"
    return TicketListResponse(
        items=items,
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links=paged_links(base, page, items_per_page, total, f"{BASE}/{event_id}"),
    )


@router.post("/{event_id}/tickets", status_code=status.HTTP_201_CREATED, response_model=TicketOut)
def create_event_ticket(
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    require_event_owner(event_id, p)
    code, res = TicketsService.create_ticket(TicketIn(event_id=event_id))
    raise_for(code, res)
    return res


def _event_ticket_or_404(event_id: int, code: str, p: Principal):
    require_event_owner(event_id, p)
    t = TicketsService.assert_can_access_ticket(code, p)
    if t.event_id != event_id:
        raise HTTPException(status_code=404, detail="Ticket not found for this event")
    return t


@router.get("/{event_id}/tickets/{code}", response_model=TicketOut)
def get_event_ticket(
    event_id: int = Path(..., ge=1),
    code: str = Path(...),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    return TicketsService.build_ticket_out(_event_ticket_or_404(event_id, code, p))


@router.delete("/{event_id}/tickets/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_ticket(
    event_id: int = Path(..., ge=1),
    code: str = Path(...),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    _event_ticket_or_404(event_id, code, p)
    TicketsService.delete_ticket(code)
    return Response(status_code=204)
