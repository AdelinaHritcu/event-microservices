from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import JSONResponse, Response
from peewee import IntegrityError

from app.controllers.deps import get_db
from app.controllers.tickets import raise_for, paged_links
from app.links import buy_ticket_link, client_links
from app.services import packages_service
from app.database.models import Package, Event
from app.dtos.packages_schemas import (
    PackageIn,
    PackageOut,
    PackageItem,
    PackageListResponse,
    Link,
)
from app.dtos.tickets_schemas import TicketIn, TicketOut, TicketListResponse
from app.services.tickets_service import TicketsService
from app.security.auth import require_roles, Principal, require_owner

BASE = "/api/event-manager/event-packets"

router = APIRouter(
    prefix=BASE,
    tags=["event-packets"],
)


def build_package_links(package_id: int) -> Dict[str, Link]:
    return {
        "self": Link(href=f"{BASE}/{package_id}", type="GET"),
        "parent": Link(href=BASE, type="GET"),
        "events": Link(href=f"{BASE}/{package_id}/events", type="GET"),
        "tickets": Link(href=f"{BASE}/{package_id}/tickets", type="GET"),
        **{k: Link(**v) for k, v in {**buy_ticket_link(), **client_links()}.items()},
    }


def build_package_item(package: Package, available: Optional[int]) -> PackageItem:
    return PackageItem(
        id=package.id,
        id_owner=package.id_owner,
        name=package.name,
        location=package.location,
        description=package.description,
        total_seats=package.total_seats,
        available_tickets=available,
        links=build_package_links(package.id),
    )


def build_package_out(package: Package, available: Optional[int]) -> PackageOut:
    return PackageOut(**build_package_item(package, available).model_dump())


def build_event_resource(event: Event) -> Dict[str, Any]:
    base = "/api/event-manager/events"
    return {
        "id": event.id,
        "id_owner": event.id_owner,
        "name": event.name,
        "location": event.location,
        "description": event.description,
        "total_seats": event.total_seats,
        "_links": {
            "self": {"href": f"{base}/{event.id}", "type": "GET"},
            "parent": {"href": base, "type": "GET"},
        },
    }


def get_package_or_404(package_id: int) -> Package:
    package = packages_service.get_package(package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")
    return package


def require_package_owner(package_id: int, p: Principal) -> Package:
    package = get_package_or_404(package_id)
    require_owner(str(package.id_owner), p)
    return package


# ------------------------------------------------------------- packets

@router.get("", response_model=PackageListResponse)
def list_event_packets(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    available_tickets: Optional[int] = Query(None, ge=0, description="Minimum available tickets"),
    event_type: Optional[str] = Query(None, alias="type", description="Partial match in description"),
    event_name: Optional[str] = Query(None, description="Partial match on included events' names"),
    name: Optional[str] = Query(None, description="Partial match on package name"),
    location: Optional[str] = Query(None, description="Partial match on location"),
    id_owner: Optional[int] = Query(None, ge=1, description="Only packages created by this owner"),
    db=Depends(get_db),
):
    """Public: guests can browse event packages (Lab 6)."""
    rows, total = packages_service.list_packages(
        page=page,
        per_page=items_per_page,
        available_tickets=available_tickets,
        type_query=event_type,
        event_name=event_name,
        name=name,
        location=location,
        id_owner=id_owner,
    )

    q = ""
    for key, val in (
        ("available_tickets", available_tickets),
        ("type", event_type),
        ("event_name", event_name),
        ("name", name),
        ("location", location),
        ("id_owner", id_owner),
    ):
        if val is not None and val != "":
            q += f"&{key}={val}"

    return PackageListResponse(
        items=[build_package_item(pkg, av) for pkg, av in rows],
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links={**paged_links(BASE, page, items_per_page, total, "/api/event-manager", q), **client_links()},
    )


@router.get("/{package_id}", response_model=PackageOut)
def get_event_packet(package_id: int = Path(..., ge=1), db=Depends(get_db)):
    package = get_package_or_404(package_id)
    return build_package_out(package, packages_service.compute_available_tickets(package))


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PackageOut)
def create_event_packet(
    payload: PackageIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    # ID_OWNER is always taken from the JWS (Lab 4 / 3.2.2)
    owner_id = int(p.sub)
    try:
        package = packages_service.create_package(
            id_owner=owner_id,
            name=payload.name,
            location=payload.location,
            description=payload.description,
            total_seats=payload.total_seats,
        )
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Package name already exists")
    return build_package_out(package, packages_service.compute_available_tickets(package))


@router.put(
    "/{package_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={201: {"model": PackageOut, "description": "Created at the given id"}, 204: {"description": "Replaced"}},
)
def put_event_packet(
    payload: PackageIn,
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    """Lab 2: PUT creates the resource (201) or replaces it (204)."""
    if packages_service.get_package(package_id) is None:
        try:
            created = packages_service.create_package(
                id_owner=int(p.sub),
                name=payload.name,
                location=payload.location,
                description=payload.description,
                total_seats=payload.total_seats,
                package_id=package_id,
            )
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Package name already exists")
        body = build_package_out(created, packages_service.compute_available_tickets(created)).model_dump(by_alias=True)
        return JSONResponse(status_code=201, content=body, headers={"Location": f"{BASE}/{package_id}"})

    package = require_package_owner(package_id, p)
    try:
        code, res = packages_service.update_package(
            package=package,
            name=payload.name,
            location=payload.location,
            description=payload.description,
            total_seats=payload.total_seats,
        )
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Package name already exists")
    raise_for(code, res)
    # Lab 2: PUT that replaces an existing resource -> 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_packet(
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    package = require_package_owner(package_id, p)
    if packages_service.delete_package(package) == 409:
        raise HTTPException(status_code=409, detail="Delete blocked: tickets already sold")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------- packet <-> events

@router.get("/{package_id}/events")
def list_events_for_event_packet(package_id: int = Path(..., ge=1), db=Depends(get_db)):
    get_package_or_404(package_id)
    events = packages_service.list_events_for_package(package_id)
    return {
        "items": [build_event_resource(e) for e in events],
        "_links": {
            "self": {"href": f"{BASE}/{package_id}/events", "type": "GET"},
            "parent": {"href": f"{BASE}/{package_id}", "type": "GET"},
        },
    }


@router.put(
    "/{package_id}/events/{event_id}",
    status_code=status.HTTP_201_CREATED,
    responses={204: {"description": "Already linked"}},
)
def add_event_to_event_packet(
    package_id: int = Path(..., ge=1),
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    """Include an event in the package. Package seats must stay <= every event's seats."""
    package = require_package_owner(package_id, p)
    code, detail = packages_service.add_event_to_package(package, event_id)
    raise_for(code, detail)
    if code == 204:
        return Response(status_code=204)
    return {
        "package_id": package_id,
        "event_id": event_id,
        "_links": {
            "self": {"href": f"{BASE}/{package_id}/events/{event_id}", "type": "PUT"},
            "parent": {"href": f"{BASE}/{package_id}/events", "type": "GET"},
            "event": {"href": f"/api/event-manager/events/{event_id}", "type": "GET"},
        },
    }


@router.delete("/{package_id}/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event_from_event_packet(
    package_id: int = Path(..., ge=1),
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    package = require_package_owner(package_id, p)
    code, detail = packages_service.remove_event_from_package(package, event_id)
    raise_for(code, detail)
    return Response(status_code=204)


# ------------------------------------------------------------- tickets

@router.get("/{package_id}/tickets", response_model=TicketListResponse)
def list_package_tickets(
    package_id: int = Path(..., ge=1),
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    require_package_owner(package_id, p)
    items, total = TicketsService.list_tickets(
        page=page, per_page=items_per_page, package_id=package_id
    )
    base = f"{BASE}/{package_id}/tickets"
    return TicketListResponse(
        items=items,
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links=paged_links(base, page, items_per_page, total, f"{BASE}/{package_id}"),
    )


@router.post("/{package_id}/tickets", status_code=status.HTTP_201_CREATED, response_model=TicketOut)
def create_package_ticket(
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    require_package_owner(package_id, p)
    code, res = TicketsService.create_ticket(TicketIn(package_id=package_id))
    raise_for(code, res)
    return res


def _package_ticket_or_404(package_id: int, code: str, p: Principal):
    require_package_owner(package_id, p)
    t = TicketsService.assert_can_access_ticket(code, p)
    if t.package_id != package_id:
        raise HTTPException(status_code=404, detail="Ticket not found for this package")
    return t


@router.get("/{package_id}/tickets/{code}", response_model=TicketOut)
def get_package_ticket(
    package_id: int = Path(..., ge=1),
    code: str = Path(...),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    return TicketsService.build_ticket_out(_package_ticket_or_404(package_id, code, p))


@router.delete("/{package_id}/tickets/{code}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package_ticket(
    package_id: int = Path(..., ge=1),
    code: str = Path(...),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("owner-event")),
):
    _package_ticket_or_404(package_id, code, p)
    TicketsService.delete_ticket(code)
    return Response(status_code=204)
