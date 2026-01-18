from typing import Optional, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Request, status

from app.controllers.deps import get_db
from app.dtos.events_schemas import (
    EventIn,
    EventOut,
    EventItem,
    EventListResponse,
    Link,
)
from app.dtos.packages_schemas import PackageListResponse, PackageItem
from app.dtos.tickets_schemas import TicketListResponse, TicketIn, TicketOut
from app.services import events_service, packages_service
from app.services.tickets_service import TicketsService
from app.security.auth import require_roles, Principal, require_owner_or_admin

router = APIRouter(
    prefix="/api/event-manager/events",
    tags=["events"],
)


def build_event_links(event_id: int) -> Dict[str, Link]:
    return {
        "self": Link(href=f"/api/event-manager/events/{event_id}", type="GET"),
        "parent": Link(href="/api/event-manager/events", type="GET"),
    }


@router.get("", response_model=EventListResponse)
def list_events(
    request: Request,
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    name: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    db=Depends(get_db),
):
    try:
        rows, total = events_service.list_events(
            page=page,
            per_page=items_per_page,
            name=name,
            location=location,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    items: List[EventItem] = []
    for row in rows:
        event_id = row["id"]
        item_links = build_event_links(event_id)

        items.append(
            EventItem(
                id=row["id"],
                id_owner=row["id_owner"],
                name=row["name"],
                location=row["location"],
                description=row.get("description"),
                total_seats=row.get("total_seats"),
                available_seats=row.get("available_seats"),
                links=item_links,
            )
        )

    base = "/api/event-manager/events"
    q_name = "" if not name else f"&name={name}"
    q_loc = "" if not location else f"&location={location}"

    offset = (page - 1) * items_per_page
    has_next = offset + items_per_page < total

    self_href = f"{base}?page={page}&items_per_page={items_per_page}{q_name}{q_loc}"
    next_href = (
        f"{base}?page={page + 1}&items_per_page={items_per_page}{q_name}{q_loc}"
        if has_next
        else None
    )
    prev_href = (
        f"{base}?page={page - 1}&items_per_page={items_per_page}{q_name}{q_loc}"
        if page > 1
        else None
    )

    collection_links: Dict[str, Link] = {
        "self": Link(href=self_href, type="GET"),
        "parent": Link(href="/api/event-manager", type="GET"),
    }
    if next_href:
        collection_links["next"] = Link(href=next_href, type="GET")
    if prev_href:
        collection_links["prev"] = Link(href=prev_href, type="GET")

    return EventListResponse(
        items=items,
        page=page,
        items_per_page=items_per_page,
        total=total,
        links=collection_links,
    )


@router.get("/{event_id}", response_model=EventOut)
def get_event(
    event_id: int,
    db=Depends(get_db),
):
    try:
        res = events_service.get_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not res:
        raise HTTPException(status_code=404, detail="Event not found")

    links = build_event_links(event_id)

    return EventOut(
        id=res["id"],
        id_owner=res["id_owner"],
        name=res["name"],
        location=res["location"],
        description=res.get("description"),
        total_seats=res.get("total_seats"),
        available_seats=res.get("available_seats"),
        links=links,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventOut)
def create_event(
    data: EventIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    try:
        created = events_service.create_event(data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    event_id = created.get("id")
    links = build_event_links(event_id)

    return EventOut(
        id=created["id"],
        id_owner=created["id_owner"],
        name=created["name"],
        location=created["location"],
        description=created.get("description"),
        total_seats=created.get("total_seats"),
        available_seats=created.get("available_seats"),
        links=links,
    )


@router.put("/{event_id}", response_model=EventOut)
def update_event(
    event_id: int,
    data: EventIn,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    try:
        current = events_service.get_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not current:
        raise HTTPException(status_code=404, detail="Event not found")

    require_owner_or_admin(str(current["id_owner"]), p)

    try:
        code, res = events_service.update_event(event_id, data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if code == 404:
        raise HTTPException(status_code=404, detail="Event not found")
    if code == 409:
        raise HTTPException(
            status_code=409,
            detail="Edit locked: tickets already sold",
        )

    links = build_event_links(event_id)

    return EventOut(
        id=res["id"],
        id_owner=res["id_owner"],
        name=res["name"],
        location=res["location"],
        description=res.get("description"),
        total_seats=res.get("total_seats"),
        available_seats=res.get("available_seats"),
        links=links,
    )


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    try:
        current = events_service.get_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not current:
        raise HTTPException(status_code=404, detail="Event not found")

    require_owner_or_admin(str(current["id_owner"]), p)

    try:
        code = events_service.delete_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if code == 404:
        raise HTTPException(status_code=404, detail="Event not found")
    if code == 409:
        raise HTTPException(
            status_code=409,
            detail="Delete blocked: tickets already sold",
        )
    return None


@router.get("/{event_id}/event-packets", response_model=PackageListResponse)
def list_event_packets_for_event(
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
):
    try:
        e = events_service.get_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found",
        )

    try:
        packages = packages_service.list_packages_for_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    items: list[PackageItem] = []
    for pck in packages:
        try:
            available = packages_service.compute_available_tickets(pck)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=500, detail="Internal server error")

        items.append(
            PackageItem(
                id=pck.id,
                id_owner=pck.id_owner,
                name=pck.name,
                location=pck.location,
                description=pck.description,
                total_seats=pck.total_seats,
                available_tickets=available,
                links={
                    "self": Link(
                        href=f"/api/event-manager/event-packets/{pck.id}",
                        type="GET",
                    ),
                    "parent": Link(
                        href="/api/event-manager/event-packets",
                        type="GET",
                    ),
                    "events": Link(
                        href=f"/api/event-manager/event-packets/{pck.id}/events",
                        type="GET",
                    ),
                },
            )
        )

    return PackageListResponse(
        items=items,
        page=1,
        items_per_page=len(items),
        total_items=len(items),
        links={
            "self": Link(href=f"/api/event-manager/events/{event_id}/event-packets"),
            "parent": Link(href=f"/api/event-manager/events/{event_id}"),
        },
    )


@router.get("/{event_id}/tickets", response_model=TicketListResponse)
def list_event_tickets(
    event_id: int = Path(..., ge=1),
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    try:
        e = events_service.get_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not e:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        items, total = TicketsService.list_tickets(
            page=page,
            per_page=items_per_page,
            event_id=event_id,
            package_id=None,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    base = f"/api/event-manager/events/{event_id}/tickets"
    offset = (page - 1) * items_per_page
    has_next = offset + items_per_page < total

    self_href = f"{base}?page={page}&items_per_page={items_per_page}"
    next_href = (
        f"{base}?page={page + 1}&items_per_page={items_per_page}"
        if has_next
        else None
    )
    prev_href = (
        f"{base}?page={page - 1}&items_per_page={items_per_page}"
        if page > 1
        else None
    )

    collection_links: Dict[str, Link] = {
        "self": Link(href=self_href, type="GET"),
        "parent": Link(href=f"/api/event-manager/events/{event_id}", type="GET"),
    }
    if next_href:
        collection_links["next"] = Link(href=next_href, type="GET")
    if prev_href:
        collection_links["prev"] = Link(href=prev_href, type="GET")

    return TicketListResponse(
        items=items,
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links=collection_links,
    )


@router.post(
    "/{event_id}/tickets",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketOut,
)
def create_event_ticket(
    event_id: int = Path(..., ge=1),
    db=Depends(get_db),
    p: Principal = Depends(require_roles("admin", "owner-event")),
):
    try:
        e = events_service.get_event(event_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not e:
        raise HTTPException(status_code=404, detail="Event not found")

    data = TicketIn(package_id=None, event_id=event_id)

    try:
        status_code_result, result = TicketsService.create_ticket(data)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if status_code_result == 404:
        raise HTTPException(status_code=404, detail=result["detail"])
    if status_code_result == 409:
        raise HTTPException(status_code=409, detail=result["detail"])

    return result
