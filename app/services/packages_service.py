from typing import Optional
from app.repositories import packages_repo

def _links(p_id:int):
    base = f"/api/event-manager/packages/{p_id}"
    return {
        "self": {"href": base, "type": "GET"},
        "parent": {"href": "/api/event-manager/packages", "type": "GET"},
        "events": {"href": f"{base}/events", "type": "GET"},
    }

def list_packages(*, page:int, per_page:int, name:Optional[str], location:Optional[str]):
    items, total = packages_repo.list_packages(name=name, location=location, page=page, per_page=per_page)
    payload = [ {"id":p.id,"id_owner":p.id_owner,"name":p.name,"location":p.location,
                 "description":p.description,"_links":_links(p.id)} for p in items ]
    return {"total": total, "page": page, "items_per_page": per_page, "items": payload}

def get_package(pkg_id:int):
    p = packages_repo.get_package(pkg_id)
    if not p: return None
    return {"id":p.id,"id_owner":p.id_owner,"name":p.name,"location":p.location,
            "description":p.description,"_links":_links(p.id)}

def create_package(data):
    p = packages_repo.create_package(data.dict())
    return get_package(p.id)

def update_package(pkg_id:int, data):
    p = packages_repo.update_package(pkg_id, {k:v for k,v in data.dict().items() if v is not None})
    if not p: return 404, None
    return 200, get_package(pkg_id)

def delete_package(pkg_id:int):
    return 204 if packages_repo.delete_package(pkg_id) else 404

def add_event(pkg_id:int, event_id:int, allocated_seats:int|None=None):
    ok = packages_repo.add_event_to_package(pkg_id, event_id, allocated_seats)
    return 204 if ok else 404

def list_events(pkg_id:int):
    events = packages_repo.list_events_for_package(pkg_id)
    return [{"id":e.id,"name":e.name,"location":e.location}] if events else []
