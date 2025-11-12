from typing import List, Optional, Tuple
from app.database.models import Package, EventPackage, Event

def list_packages(*, name:Optional[str]=None, location:Optional[str]=None,
                  page:int=0, per_page:int=10) -> Tuple[List[Package], int]:
    q = Package.select()
    if name:
        q = q.where(Package.name.contains(name))
    if location:
        q = q.where(Package.location == location)
    total = q.count()
    items = q.order_by(Package.id.asc()).paginate(page + 1, per_page)
    return list(items), total

def get_package(pkg_id:int) -> Optional[Package]:
    return Package.get_or_none(Package.id == pkg_id)

def create_package(data:dict) -> Package:
    return Package.create(**data)

def update_package(pkg_id:int, data:dict) -> Optional[Package]:
    p = get_package(pkg_id)
    if not p: return None
    Package.update(**data).where(Package.id == pkg_id).execute()
    p.refresh()
    return p

def delete_package(pkg_id:int) -> bool:
    return Package.delete().where(Package.id == pkg_id).execute() > 0

def add_event_to_package(pkg_id:int, event_id:int, allocated_seats:int|None=None) -> bool:
    p = get_package(pkg_id); e = Event.get_or_none(Event.id == event_id)
    if not p or not e: return False
    EventPackage.insert(package=p.id, event=e.id, allocated_seats=allocated_seats).on_conflict_ignore().execute()
    return True

def list_events_for_package(pkg_id:int) -> List[Event]:
    return [link.event for link in EventPackage.select().where(EventPackage.package == pkg_id).join(Event)]
