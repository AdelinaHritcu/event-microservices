from typing import Optional

from app.repositories.events_repo import EventsRepository
from app.repositories.packages_repo import PackagesRepository


def _links(e_id: int):
    base = f"/api/event-manager/events/{e_id}"
    return {
        "self": {"href": base, "type": "GET"},
        "parent": {"href": "/api/event-manager/events", "type": "GET"},
        "tickets": {"href": f"{base}/tickets", "type": "GET"},
        "event-packets": {"href": f"{base}/event-packets", "type": "GET"},
    }


def _to_dict(e):
    sold = EventsRepository.count_sold_event_tickets(e.id)
    available = None if e.total_seats is None else max(e.total_seats - sold, 0)
    return {
        "id": e.id,
        "id_owner": e.id_owner,
        "name": e.name,
        "location": e.location,
        "description": e.description,
        "total_seats": e.total_seats,
        "available_seats": available,
        "_links": _links(e.id),
    }


def list_events(
    page: int,
    per_page: int,
    name: Optional[str] = None,
    location: Optional[str] = None,
    available_tickets: Optional[int] = None,
):
    events, total = EventsRepository.list_events(
        name=name,
        location=location,
        available_tickets=available_tickets,
        page=page,
        per_page=per_page,
    )
    return [_to_dict(e) for e in events], total


def get_event(event_id: int):
    e = EventsRepository.get_by_id(event_id)
    if not e:
        return None
    return _to_dict(e)


def create_event(data, owner_id: int):
    payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    payload["id_owner"] = owner_id
    e = EventsRepository.create_event(payload)
    return get_event(e.id)


def update_event(event_id: int, data, owner_id: Optional[int] = None):
    """Returns (status_code, event_dict | detail_str)."""
    current = EventsRepository.get_by_id(event_id)
    if not current:
        return 404, "Event not found"

    payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    payload = {k: v for k, v in payload.items() if v is not None}
    if owner_id is not None:
        # owner-event cannot transfer ownership
        payload["id_owner"] = owner_id

    new_seats = payload.get("total_seats", current.total_seats)
    if new_seats != current.total_seats:
        if EventsRepository.count_sold_event_tickets(event_id) > 0:
            return 409, "Edit locked: tickets already sold for this event"
        # a package cannot offer more seats than any of its events
        for pkg in PackagesRepository.list_packages_for_event(event_id):
            if pkg.total_seats is not None and new_seats < pkg.total_seats:
                return 409, (
                    f"Package '{pkg.name}' has {pkg.total_seats} seats; "
                    f"event seats cannot go below that"
                )

    EventsRepository.update_event(event_id, payload)
    return 200, get_event(event_id)


def delete_event(event_id: int):
    if EventsRepository.count_sold_event_tickets(event_id) > 0:
        return 409
    for pkg in PackagesRepository.list_packages_for_event(event_id):
        if PackagesRepository.count_sold_tickets(pkg) > 0:
            return 409
    return 204 if EventsRepository.delete_event(event_id) else 404
