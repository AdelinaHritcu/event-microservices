from app.repositories import tickets_repo
from app.repositories import events_repo

def _links(code:str):
    base = f"/api/event-manager/tickets/{code}"
    return {"self":{"href":base,"type":"GET"}, "parent":{"href":"/api/event-manager/tickets","type":"GET"}}

def list_tickets(page:int, per_page:int):
    items, total = tickets_repo.list_tickets(page=page, per_page=per_page)
    payload = [ {"code":t.code, "event_id":t.event_id, "package_id":t.package_id, "_links":_links(t.code)} for t in items ]
    return {"total": total, "page": page, "items_per_page": per_page, "items": payload}

def get_ticket(code:str):
    t = tickets_repo.get_ticket(code)
    if not t: return None
    return {"code":t.code, "event_id":t.event_id, "package_id":t.package_id, "_links":_links(t.code)}

def create_ticket(data):
    if data.event_id is not None:
        sold = events_repo.count_sold_event_tickets(data.event_id)
        ev = events_repo.get_event(data.event_id)
        if not ev: return 404, None
        if ev.total_seats is not None and sold >= ev.total_seats:
            return 409, None
    t = tickets_repo.create_ticket(data.dict())
    return 201, get_ticket(t.code)

def delete_ticket(code:str):
    return 204 if tickets_repo.delete_ticket(code) else 404
