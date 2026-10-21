from typing import Optional
from peewee import JOIN
from app.database.models import Ticket, Event, Package


class TicketsRepository:

    @staticmethod
    def create(data: dict) -> Ticket:
        return Ticket.create(**data)

    @staticmethod
    def get_by_code(code: str) -> Optional[Ticket]:
        return Ticket.get_or_none(Ticket.code == code)

    @staticmethod
    def list_tickets(
            page: int,
            per_page: int,
            event_id: int | None = None,
            package_id: int | None = None,
            owner_id: int | None = None,
    ) -> tuple[list[Ticket], int]:
        q = Ticket.select().order_by(Ticket.code.asc())
        if event_id is not None:
            q = q.where(Ticket.event == event_id)
        if package_id is not None:
            q = q.where(Ticket.package == package_id)
        if owner_id is not None:
            # only tickets for events/packages owned by this user
            q = (
                q.join(Event, JOIN.LEFT_OUTER, on=(Ticket.event == Event.id))
                 .switch(Ticket)
                 .join(Package, JOIN.LEFT_OUTER, on=(Ticket.package == Package.id))
                 .where((Event.id_owner == owner_id) | (Package.id_owner == owner_id))
            )
        total = q.count()
        items = q.paginate(page, per_page)
        return list(items), total

    @staticmethod
    def delete(code: str) -> bool:
        return Ticket.delete().where(Ticket.code == code).execute() > 0
