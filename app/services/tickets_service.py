from typing import Optional, Tuple, List
import uuid

from peewee import IntegrityError, fn

from app.repositories.tickets_repo import TicketsRepository
from app.database.models import Ticket, Package, Event
from app.dtos.tickets_schemas import TicketIn, TicketOut, TicketItem, Link


def build_ticket_links(code: str) -> dict[str, Link]:
    base = "/api/event-manager/tickets"
    return {
        "self": Link(href=f"{base}/{code}", type="GET"),
        "parent": Link(href=base, type="GET"),
    }


def build_ticket_item(t: Ticket) -> TicketItem:
    return TicketItem(
        code=t.code,
        package_id=t.package.id if t.package else None,
        event_id=t.event.id if t.event else None,
        links=build_ticket_links(t.code),
    )


def build_ticket_out(t: Ticket) -> TicketOut:
    return TicketOut(
        code=t.code,
        package_id=t.package.id if t.package else None,
        event_id=t.event.id if t.event else None,
        links=build_ticket_links(t.code),
    )


def list_tickets(
    page: int,
    per_page: int,
    event_id: Optional[int] = None,
    package_id: Optional[int] = None,
) -> Tuple[List[TicketItem], int]:
    items, total = TicketsRepository.list_tickets(
        page=page,
        per_page=per_page,
        event_id=event_id,
        package_id=package_id,
    )
    return [build_ticket_item(t) for t in items], total


def get_ticket(code: str) -> Optional[TicketOut]:
    t = TicketsRepository.get_by_code(code)
    if not t:
        return None
    return build_ticket_out(t)


def _check_capacity_for_package(package_id: int) -> Tuple[bool, Optional[int], Optional[int]]:
    package = Package.get_or_none(Package.id == package_id)
    if package is None:
        return False, None, None
    if package.total_seats is None:
        return True, None, None
    current = (
        Ticket.select(fn.COUNT(Ticket.code))
        .where(Ticket.package == package)
        .scalar()
    )
    return current < package.total_seats, current, package.total_seats


def _check_capacity_for_event(event_id: int) -> Tuple[bool, Optional[int], Optional[int]]:
    event = Event.get_or_none(Event.id == event_id)
    if event is None:
        return False, None, None
    if event.total_seats is None:
        return True, None, None
    current = (
        Ticket.select(fn.COUNT(Ticket.code))
        .where(Ticket.event == event)
        .scalar()
    )
    return current < event.total_seats, current, event.total_seats


def create_ticket(data: TicketIn) -> Tuple[int, dict | TicketOut]:
    if (data.package_id is None and data.event_id is None) or (
        data.package_id is not None and data.event_id is not None
    ):
        return 409, {
            "detail": "Exactly one of package_id or event_id must be provided."
        }

    if data.package_id is not None:
        ok, current, max_seats = _check_capacity_for_package(data.package_id)
        if ok is False and current is None and max_seats is None:
            return 404, {"detail": "Package not found."}
        if ok is False and current is not None and max_seats is not None:
            return 409, {
                "detail": "No more available seats for this package.",
                "current_tickets": current,
                "total_seats": max_seats,
            }

    if data.event_id is not None:
        ok, current, max_seats = _check_capacity_for_event(data.event_id)
        if ok is False and current is None and max_seats is None:
            return 404, {"detail": "Event not found."}
        if ok is False and current is not None and max_seats is not None:
            return 409, {
                "detail": "No more available seats for this event.",
                "current_tickets": current,
                "total_seats": max_seats,
            }

    generated_code = uuid.uuid4().hex[:10].upper()

    payload = {
        "code": generated_code,
        "package": data.package_id,
        "event": data.event_id,
    }

    try:
        t = TicketsRepository.create(payload)
    except IntegrityError:
        return 409, {"detail": "Ticket code already exists, please retry."}

    return 201, build_ticket_out(t)


def delete_ticket(code: str) -> Tuple[int, Optional[dict]]:
    deleted = TicketsRepository.delete(code)
    if deleted:
        return 204, None
    return 404, {"detail": "Ticket not found"}
