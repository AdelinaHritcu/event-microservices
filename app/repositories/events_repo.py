from typing import List, Optional, Tuple
from peewee import fn
from app.database.models import Event, Ticket

def list_events(*, name: Optional[str]=None, location: Optional[str]=None,
                page:int=0, per_page:int=10) -> Tuple[List[Event], int]:
    q = Event.select()
    if name:
        q = q.where(Event.name.contains(name))
    if location:
        q = q.where(Event.location == location)
    total = q.count()
    items = q.order_by(Event.id.asc()).paginate(page + 1, per_page)
    return list(items), total

def get_event(event_id:int) -> Optional[Event]:
    return Event.get_or_none(Event.id == event_id)

def create_event(data:dict) -> Event:
    return Event.create(**data)

def update_event(event_id:int, data:dict) -> Optional[Event]:
    ev = get_event(event_id)
    if not ev: return None
    q = Event.update(**data).where(Event.id == event_id)
    q.execute()
    ev.refresh()
    return ev

def delete_event(event_id:int) -> bool:
    deleted = Event.delete().where(Event.id == event_id).execute()
    return deleted > 0

def count_sold_event_tickets(event_id:int) -> int:
    return Ticket.select(fn.COUNT(Ticket.code)).where(Ticket.event == event_id).scalar() or 0
