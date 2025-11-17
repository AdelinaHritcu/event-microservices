from typing import Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.controllers.deps import get_db
from app.services import packages_service
from app.database.models import Package, Event


router = APIRouter(
    prefix="/api/event-manager/event-packets",
    tags=["event-packets"],
)


class PackageIn(BaseModel):
    id_owner: int
    name: str = Field(max_length=128)
    location: str = Field(max_length=128)
    description: Optional[str] = None
    total_seats: Optional[int] = Field(default=None, ge=0)


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(default=None, max_length=128)
    location: Optional[str] = Field(default=None, max_length=128)
    description: Optional[str] = None
    total_seats: Optional[int] = Field(default=None, ge=0)


def build_package_resource(package: Package, available_tickets: Optional[int]) -> dict[str, Any]:
    base_href = "/api/event-manager/event-packets"
    return {
        "id": package.id,
        "id_owner": package.id_owner,
        "name": package.name,
        "location": package.location,
        "description": package.description,
        "total_seats": package.total_seats,
        "available_tickets": available_tickets,
        "_links": {
            "self": {"href": f"{base_href}/{package.id}"},
            "parent": {"href": base_href},
            "events": {"href": f"{base_href}/{package.id}/events"},
        },
    }


def build_event_resource(event: Event) -> dict[str, Any]:
    base_href = "/api/event-manager/events"
    return {
        "id": event.id,
        "id_owner": event.id_owner,
        "name": event.name,
        "location": event.location,
        "description": event.description,
        "total_seats": event.total_seats,
        "_links": {
            "self": {"href": f"{base_href}/{event.id}"},
            "parent": {"href": base_href},
        },
    }


@router.get("")
def list_event_packets(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    available_tickets: Optional[int] = Query(None, ge=0),
    event_type: Optional[str] = Query(None, alias="type"),
    db=Depends(get_db),
):
    rows, total = packages_service.list_packages(
        page=page,
        per_page=items_per_page,
        available_tickets=available_tickets,
        type_query=event_type,
    )

    items = [
        build_package_resource(package, available)
        for package, available in rows
    ]

    base_href = "/api/event-manager/event-packets"

    return {
        "items": items,
        "page": page,
        "items_per_page": items_per_page,
        "total_items": total,
        "_links": {
            "self": {
                "href": f"{base_href}?page={page}&items_per_page={items_per_page}"
            },
            "parent": {"href": base_href},
        },
    }


@router.get("/{package_id}")
def get_event_packet(
    package_id: int = Path(..., ge=1),
    db=Depends(get_db),
):
    try:
        package = packages_service.get_package(package_id)
    except Package.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    available = packages_service.compute_available_tickets(package)
    return build_package_resource(package, available)


@router.post("", status_code=status.HTTP_201_CREATED)
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
    return build_package_resource(package, available)


@router.put("/{package_id}")
def update_event_packet(
    package_id: int = Path(..., ge=1),
    payload: PackageUpdate = ...,
    db=Depends(get_db),
):
    try:
        package = packages_service.get_package(package_id)
    except Package.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    package = packages_service.update_package(
        package=package,
        name=payload.name,
        location=payload.location,
        description=payload.description,
        total_seats=payload.total_seats,
    )
    available = packages_service.compute_available_tickets(package)
    return build_package_resource(package, available)


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event_packet(
    package_id: int = Path(..., ge=1),
):
    try:
        package = packages_service.get_package(package_id)
    except Package.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    packages_service.delete_package(package)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{package_id}/events")
def list_events_for_event_packet(
    package_id: int = Path(..., ge=1),
):
    try:
        packages_service.get_package(package_id)
    except Package.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    events = packages_service.list_events_for_package(package_id)
    items = [build_event_resource(e) for e in events]

    base_href = "/api/event-manager/event-packets"

    return {
        "items": items,
        "_links": {
            "self": {"href": f"{base_href}/{package_id}/events"},
            "parent": {"href": f"{base_href}/{package_id}"},
        },
    }
