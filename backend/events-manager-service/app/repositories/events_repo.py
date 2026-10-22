from typing import List, Optional, Tuple
from peewee import fn
from app.database.models import Event, Ticket


class EventsRepository:

    @staticmethod
    def list_events(*, name: Optional[str] = None, location: Optional[str] = None,
                    available_tickets: Optional[int] = None,
                    id_owner: Optional[int] = None,
                    page: int = 1, per_page: int = 10) -> Tuple[List[Event], int]:
        q = Event.select()
        if name:
            q = q.where(Event.name.contains(name))
        if location:
            q = q.where(Event.location.contains(location))
        if id_owner is not None:
            q = q.where(Event.id_owner == id_owner)
        if available_tickets is not None:
            sold = (
                Ticket.select(fn.COUNT(Ticket.code))
                .where(Ticket.event == Event.id)
            )
            q = q.where(
                Event.total_seats.is_null(False)
                & ((Event.total_seats - sold) >= available_tickets)
            )

        total = q.count()
        items = q.order_by(Event.id.asc()).paginate(page, per_page)
        return list(items), total

    @staticmethod
    def get_by_id(event_id: int) -> Optional[Event]:
        return Event.get_or_none(Event.id == event_id)

    @staticmethod
    def create_event(data: dict) -> Event:
        return Event.create(**data)

    @staticmethod
    def update_event(event_id: int, data: dict) -> Optional[Event]:
        ev = Event.get_or_none(Event.id == event_id)
        if not ev:
            return None
        Event.update(**data).where(Event.id == event_id).execute()
        return ev

    @staticmethod
    def delete_event(event_id: int) -> bool:
        return Event.delete().where(Event.id == event_id).execute() > 0

    @staticmethod
    def count_sold_event_tickets(event_id: int) -> int:
        return Ticket.select(fn.COUNT(Ticket.code)).where(Ticket.event == event_id).scalar() or 0
