from typing import List, Tuple
from app.database.models import Ticket

def create_ticket(data: dict) -> Ticket:
    return Ticket.create(**data)

def get_ticket(code: str) -> Ticket | None:
    return Ticket.get_or_none(Ticket.code == code)

def list_tickets(
    page: int = 0,
    per_page: int = 10,
    event_id: int | None = None,
    package_id: int | None = None,
) -> Tuple[list[Ticket], int]:
    q = Ticket.select().order_by(Ticket.code.asc())
    if event_id is not None:
        q = q.where(Ticket.event == event_id)
    if package_id is not None:
        q = q.where(Ticket.package == package_id)
    total = q.count()
    items = q.paginate(page + 1, per_page)
    return list(items), total

def delete_ticket(code: str) -> bool:
    return Ticket.delete().where(Ticket.code == code).execute() > 0
