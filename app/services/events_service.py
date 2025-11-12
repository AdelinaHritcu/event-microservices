from typing import Optional
from app.repositories import events_repo

def _links(e_id:int):
    base = f"/api/event-manager/events/{e_id}"
    return {
        "self": {"href": base, "type": "GET"},
        "parent": {"href": "/api/event-manager/events", "type": "GET"},
        "tickets": {"href": f"{base}/tickets", "type": "GET"},
    }

def list_events(*, page:int, per_page:int, name:Optional[str], location:Optional[str]):
    items, total = events_repo.list_events(name=name, location=location, page=page, per_page=per_page)
    payload = []
    for e in items:
        sold = events_repo.count_sold_event_tickets(e.id)
        available = None if e.total_seats is None else max(e.total_seats - sold, 0)
        payload.append({
            "id": e.id, "id_owner": e.id_owner, "name": e.name, "location": e.location,
            "description": e.description, "total_seats": e.total_seats,
            "available_seats": available, "_links": _links(e.id),
        })
    return {"total": total, "page": page, "items_per_page": per_page, "items": payload}

def get_event(event_id:int):
    e = events_repo.get_event(event_id)
    if not e: return None
    sold = events_repo.count_sold_event_tickets(e.id)
    available = None if e.total_seats is None else max(e.total_seats - sold, 0)
    return {
        "id": e.id, "id_owner": e.id_owner, "name": e.name, "location": e.location,
        "description": e.description, "total_seats": e.total_seats,
        "available_seats": available, "_links": _links(e.id),
    }

def create_event(data):
    e = events_repo.create_event(data.dict())
    return get_event(e.id)

def update_event(event_id:int, data):
    sold = events_repo.count_sold_event_tickets(event_id)
    if sold > 0 and (data.total_seats is not None):
        return 409, None
    e = events_repo.update_event(event_id, {k:v for k,v in data.dict().items() if v is not None})
    if not e: return 404, None
    return 200, get_event(event_id)

def delete_event(event_id:int):
    sold = events_repo.count_sold_event_tickets(event_id)
    if sold > 0: return 409
    return 204 if events_repo.delete_event(event_id) else 404
