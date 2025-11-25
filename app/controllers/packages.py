from typing import Optional, Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import Response

from app.controllers.deps import get_db
from app.services import packages_service, tickets_service
from app.database.models import Package, Event
from app.dtos.packages_schemas import (
    PackageIn,
    PackageOut,
    PackageItem,
    PackageListResponse,
    Link,
)
from app.dtos.tickets_schemas import TicketIn


router = APIRouter(
    prefix="/api/event-manager/event-packets",
    tags=["event-packets"],
)


def build_package_links(package_id: int) -> Dict[str, Link]:
    base = "/api/event-manager/event-packets"
    return {
        "self": Link(href=f"{base}/{package_id}", type="GET"),
        "parent": Link(href=base, type="GET"),
        "events": Link(href=f"{base}/{package_id}/events", type="GET"),
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
    return PackageOut(
        id=package.id,
        id_owner=package.id_owner,
        name=package.name,
        location=package.location,
        description=package.description,
        total_seats=package.total_seats,
        available_tickets=available,
        links=build_package_links(package.id),
    )


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
            "self": {"href": f"{base}/{event.id}"},
            "parent": {"href": base},
        },
    }


@router.get("", response_model=PackageListResponse)
def list_event_packets(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    available_tickets: Optional[int] = Query(None, ge=0),
    event_type: Optional[str] = Query(None, alias="type"),
    event_name: Optional[str] = Query(None),
    db=Depends(get_db),
):
    rows, total = packages_service.list_packages(
        page=page,
        per_page=items_per_page,
        available_tickets=available_tickets,
        type_query=event_type,
        event_name=event_name,
    )

    items: List[PackageItem] = []
    for package, available in rows:
        items.append(build_package_item(package, available))

    base = "/api/event-manager/event-packets"

    q_av = "" if available_tickets is None else f"&available_tickets={available_tickets}"
    q_type = "" if not event_type else f"&type={event_type}"
    q_ev = "" if not event_name else f"&event_name={event_name}"

    self_href = (
        f"{base}?page={page}&items_per_page={items_per_page}{q_av}{q_type}{q_ev}"
    )

    return PackageListResponse(
        items=items,
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links={
            "self": Link(href=self_href, type="GET"),
            "parent": Link(href=base, type="GET"),
        },
    )


@router.get("/{package_id}", response_model=PackageOut)
def get_event_packet(
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
):
    package = packages_service.get_package(package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    available = packages_service.compute_available_tickets(package)
    return build_package_out(package, available)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PackageOut)
def create_event_packet(
    payload: PackageIn,
    db=Depends(get_db),
):
    package = packages_service.create_package(
        id_owner=payload.id_owner,
        name=payload.name,
        location=payload.location,
        description=payload.description,
        total_seats=payload.total_seats,
    )
    available = packages_service.compute_available_tickets(package)
    return build_package_out(package, available)


@router.put("/{package_id}", response_model=PackageOut)
def update_event_packet(
    package_id: int = Path(..., ge=1),
    payload: PackageIn = ...,
    db=Depends(get_db),
):
    package = packages_service.get_package(package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    updated = packages_service.update_package(
        package=package,
        name=payload.name,
        location=payload.location,
        description=payload.description,
        total_seats=payload.total_seats,
    )

    available = packages_service.compute_available_tickets(updated)
    return build_package_out(updated, available)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_packet(
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
):
    package = packages_service.get_package(package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    code = packages_service.delete_package(package)
    if code == 409:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Delete blocked: tickets already sold",
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{package_id}/events")
def list_events_for_event_packet(
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
):
    package = packages_service.get_package(package_id)
    if package is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    events = packages_service.list_events_for_package(package_id)
    items = [build_event_resource(e) for e in events]

    base = "/api/event-manager/event-packets"

    return {
        "items": items,
        "_links": {
            "self": {"href": f"{base}/{package_id}/events"},
            "parent": {"href": f"{base}/{package_id}"},
        },
    }


@router.get("/{package_id}/tickets")
def list_package_tickets(
    package_id: int,
    page: int = Query(0, ge=0),
    items_per_page: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
):
    return tickets_service.list_tickets(
        page=page,
        per_page=items_per_page,
        package_id=package_id,
    )


@router.post("/{package_id}/tickets", status_code=201)
def create_package_ticket(
    package_id: int,
    data: TicketIn,
    db=Depends(get_db),
):
    payload = data.model_copy(update={
        "package_id": package_id,
        "event_id": None,
    })

    code, res = tickets_service.create_ticket(payload)
    return res
