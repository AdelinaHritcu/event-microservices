from app.repositories import tickets_repo, events_repo
from app.dtos.schemas import TicketIn
import uuid

def _links(code: str):
    base = f"/api/event-manager/tickets/{code}"
    return {
        "self":   {"href": base, "type": "GET"},
        "parent": {"href": "/api/event-manager/tickets", "type": "GET"},
    }

def list_tickets(page: int, per_page: int,
                 event_id: int | None = None,
                 package_id: int | None = None):
    items, total = tickets_repo.list_tickets(
        page=page, per_page=per_page,
        event_id=event_id, package_id=package_id,
    )
    payload = [
        {
            "code": t.code,
            "event_id": t.event.id if t.event is not None else None,
            "package_id": t.package.id if t.package is not None else None,
            "_links": _links(t.code),
        }
        for t in items
    ]
    return {
        "total": total,
        "page": page,
        "items_per_page": per_page,
        "items": payload,
    }

def get_ticket(code: str):
    t = tickets_repo.get_ticket(code)
    if not t:
        return None
    return {
        "code": t.code,
        "event_id": t.event.id if t.event is not None else None,
        "package_id": t.package.id if t.package is not None else None,
        "_links": _links(t.code),
    }

def create_ticket(data: TicketIn):
    generated_code = uuid.uuid4().hex[:10].upper()
    payload = data.model_dump()
    payload["code"] = generated_code
    t = tickets_repo.create_ticket(payload)
    return 201, get_ticket(t.code)

def delete_ticket(code: str):
    return 204 if tickets_repo.delete_ticket(code) else 404
