from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from app.controllers.deps import get_db
from app.database.models import Event
from app.dtos.schemas import EventIn, EventOut, PackageListResponse, PackageItem
from app.services import events_service, packages_service
from app.dtos.schemas import TicketIn, TicketOut
from app.services import tickets_service

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
        page=page,
        per_page=items_per_page,
        name=name,
        location=location,
    )

    offset = (page - 1) * items_per_page
    has_next = offset + items_per_page < total

    q_name = "" if not name else f"&name={name}"
    q_loc = "" if not location else f"&location={location}"
    base = "/api/event-manager/events"

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


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: int, db=Depends(get_db)):
    res = events_service.get_event(event_id)
    if not res:
        raise HTTPException(status_code=404, detail="Event not found")

    res.setdefault("_links", {})
    res["_links"].update(
        {
            "self": {"href": f"/api/event-manager/events/{event_id}"},
            "parent": {"href": "/api/event-manager/events"},
        }
    )
    return res


@router.post("", status_code=status.HTTP_201_CREATED, response_model=EventOut)
def create_event(data: EventIn, db=Depends(get_db)):
    created = events_service.create_event(data)
    event_id = created.get("id")

    created.setdefault("_links", {})
    created["_links"].update(
        {
            "self": {
                "href": f"/api/event-manager/events/{event_id}"
            }
            if event_id is not None
            else None,
            "parent": {"href": "/api/event-manager/events"},
        }
    )
    return created


@router.put("/{event_id}", response_model=EventOut)
def update_event(event_id: int, data: EventIn, db=Depends(get_db)):
    code, res = events_service.update_event(event_id, data)

    if code == 404:
        raise HTTPException(status_code=404, detail="Event not found")
    if code == 409:
        raise HTTPException(
            status_code=409,
            detail="Edit locked: tickets already sold",
        )

    res.setdefault("_links", {})
    res["_links"].update(
        {
            "self": {"href": f"/api/event-manager/events/{event_id}"},
            "parent": {"href": "/api/event-manager/events"},
        }
    )
    return res


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(event_id: int, db=Depends(get_db)):
    code = events_service.delete_event(event_id)

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
        events_service.get_event(event_id)
    except Event.DoesNotExist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    packages = packages_service.list_packages_for_event(event_id)

    items: list[PackageItem] = []
    for p in packages:
        available = packages_service.compute_available_tickets(p)
        items.append(
            PackageItem(
                id=p.id,
                id_owner=p.id_owner,
                name=p.name,
                location=p.location,
                description=p.description,
                total_seats=p.total_seats,
                available_tickets=available,
                _links={
                    "self": {
                        "href": f"/api/event-manager/event-packets/{p.id}"
                    },
                    "parent": {
                        "href": "/api/event-manager/event-packets"
                    },
                    "events": {
                        "href": f"/api/event-manager/event-packets/{p.id}/events"
                    },
                },
            )
        )

    return PackageListResponse(
        items=items,
        page=1,
        items_per_page=len(items),
        total_items=len(items),
        _links={
            "self": {
                "href": f"/api/event-manager/events/{event_id}/event-packets"
            },
            "parent": {
                "href": f"/api/event-manager/events/{event_id}"
            },
        },
    )


@router.get("/{event_id}/tickets")
def list_event_tickets(
    event_id: int = Path(..., ge=1),
    page: int = Query(0, ge=0),
    items_per_page: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
):
    return tickets_service.list_tickets(
        page=page,
        per_page=items_per_page,
        event_id=event_id,
    )


@router.post(
    "/{event_id}/tickets",
    status_code=status.HTTP_201_CREATED,
    response_model=TicketOut,
)
def create_event_ticket(
    event_id: int,
    data: TicketIn,
    db=Depends(get_db),
):
    payload = data.model_copy(update={
        "event_id": event_id,
        "package_id": None,
    })

    code, res = tickets_service.create_ticket(payload)
    if code == 404:
        raise HTTPException(status_code=404, detail="Event not found")
    if code == 409:
        raise HTTPException(status_code=409, detail="No more seats available for event")
    return res
