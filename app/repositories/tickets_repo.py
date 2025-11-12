from typing import List, Optional, Tuple
from app.database.models import Ticket

def create_ticket(data:dict) -> Optional[Ticket]:
    return Ticket.create(**data)

def get_ticket(code:str) -> Optional[Ticket]:
    return Ticket.get_or_none(Ticket.code == code)

def list_tickets(page:int=0, per_page:int=10) -> Tuple[List[Ticket], int]:
    q = Ticket.select().order_by(Ticket.code.asc())
    total = q.count()
    items = q.paginate(page + 1, per_page)
    return list(items), total

def delete_ticket(code:str) -> bool:
    return Ticket.delete().where(Ticket.code == code).execute() > 0
