from typing import Optional

from app.repositories.events_repo import EventsRepository


def _links(e_id: int):
    base = f"/api/event-manager/events/{e_id}"
    return {
        "self": {"href": base, "type": "GET"},
        "parent": {"href": "/api/event-manager/events", "type": "GET"},
        "tickets": {"href": f"{base}/tickets", "type": "GET"},
    }


def list_events(
    page: int,
    per_page: int,
    name: Optional[str] = None,
    location: Optional[str] = None,
):
    events, total = EventsRepository.list_events(
        name=name,
        location=location,
        page=page,
        per_page=per_page,
    )

    result = []

    for e in events:
        sold = EventsRepository.count_sold_event_tickets(e.id)
        available = None if e.total_seats is None else max(e.total_seats - sold, 0)

        result.append(
            {
                "id": e.id,
                "id_owner": e.id_owner,
                "name": e.name,
                "location": e.location,
                "description": e.description,
                "total_seats": e.total_seats,
                "available_seats": available,
                "_links": _links(e.id),
            }
        )

    return result, total


def get_event(event_id: int):
    e = EventsRepository.get_by_id(event_id)
    if not e:
        return None
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


def create_event(data):
    payload = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    e = EventsRepository.create_event(payload)
    return get_event(e.id)


def update_event(event_id: int, data):
    sold = EventsRepository.count_sold_event_tickets(event_id)
    if sold > 0 and (data.total_seats is not None):
        return 409, None

    if hasattr(data, "model_dump"):
        payload = data.model_dump()
    else:
        payload = data.dict()

    e = EventsRepository.update_event(
        event_id,
        {k: v for k, v in payload.items() if v is not None},
    )
    if not e:
        return 404, None
    return 200, get_event(event_id)


def delete_event(event_id: int):
    sold = EventsRepository.count_sold_event_tickets(event_id)
    if sold > 0:
        return 409
    return 204 if EventsRepository.delete_event(event_id) else 404
