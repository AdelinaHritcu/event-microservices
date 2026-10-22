from __future__ import annotations

from typing import Optional, Tuple, List
import uuid

from fastapi import HTTPException
from peewee import IntegrityError, fn

from app.database.mariadb_connection import db
from app.repositories.tickets_repo import TicketsRepository
from app.database.models import Ticket, Package, Event, EventPackage
from app.dtos.tickets_schemas import TicketIn, TicketOut, TicketItem, Link
from app.security.auth import Principal


class TicketsService:

    @staticmethod
    def _is_admin(p: Principal) -> bool:
        return getattr(p, "role", None) == "admin"

    @staticmethod
    def _principal_user_id(p: Principal) -> int:
        try:
            return int(p.sub)
        except (TypeError, ValueError, AttributeError):
            raise HTTPException(status_code=401, detail="Unauthenticated")

    @staticmethod
    def build_ticket_links(t: Ticket) -> dict[str, Link]:
        base = "/api/event-manager/tickets"
        links = {
            "self": Link(href=f"{base}/{t.code}", type="GET"),
            "parent": Link(href=base, type="GET"),
        }
        if t.event_id is not None:
            links["event"] = Link(href=f"/api/event-manager/events/{t.event_id}", type="GET")
        if t.package_id is not None:
            links["event-packet"] = Link(
                href=f"/api/event-manager/event-packets/{t.package_id}", type="GET"
            )
        return links

    @staticmethod
    def build_ticket_item(t: Ticket) -> TicketItem:
        return TicketItem(
            code=t.code,
            package_id=t.package_id,
            event_id=t.event_id,
            links=TicketsService.build_ticket_links(t),
        )

    @staticmethod
    def build_ticket_out(t: Ticket) -> TicketOut:
        return TicketOut(
            code=t.code,
            package_id=t.package_id,
            event_id=t.event_id,
            links=TicketsService.build_ticket_links(t),
        )

    # ---------- authorization helpers ----------

    @staticmethod
    def get_by_code_or_404(code: str) -> Ticket:
        t = TicketsRepository.get_by_code(code)
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return t

    @staticmethod
    def assert_can_access_ticket(code: str, p: Principal) -> Ticket:
        t = TicketsRepository.get_by_code(code)
        if not t:
            raise HTTPException(status_code=404, detail="Ticket not found")
        if TicketsService._is_admin(p):
            return t

        uid = TicketsService._principal_user_id(p)
        target = t.event if t.event_id is not None else t.package
        if target is None:
            raise HTTPException(status_code=400, detail="Invalid ticket linkage")
        if int(target.id_owner) != uid:
            raise HTTPException(status_code=403, detail="Forbidden: not owner")
        return t

    @staticmethod
    def assert_can_manage_ticket_target(
        p: Principal,
        *,
        event_id: Optional[int],
        package_id: Optional[int],
    ) -> None:
        if event_id is not None:
            target = Event.get_or_none(Event.id == event_id)
            if target is None:
                raise HTTPException(status_code=404, detail="Event not found")
        elif package_id is not None:
            target = Package.get_or_none(Package.id == package_id)
            if target is None:
                raise HTTPException(status_code=404, detail="Package not found")
        else:
            raise HTTPException(status_code=400, detail="Provide event_id or package_id")

        if TicketsService._is_admin(p):
            return
        if int(target.id_owner) != TicketsService._principal_user_id(p):
            raise HTTPException(status_code=403, detail="Forbidden: not owner")

    # ---------- capacity ----------

    @staticmethod
    def _capacity_error(
        event_id: Optional[int], package_id: Optional[int]
    ) -> Optional[Tuple[int, dict]]:
        """
        Must be called inside a transaction: the target row is locked with
        SELECT ... FOR UPDATE so concurrent sales cannot exceed the limit.
        """
        if package_id is not None:
            model, field, label = Package, Ticket.package, "package"
            target_id = package_id
        else:
            model, field, label = Event, Ticket.event, "event"
            target_id = event_id

        target = model.select().where(model.id == target_id).for_update().first()
        if target is None:
            return 404, {"detail": f"{label.capitalize()} not found."}
        if target.total_seats is None:
            return 409, {"detail": f"This {label} has no seats configured; tickets cannot be sold."}
        if package_id is not None and not EventPackage.select().where(EventPackage.package == package_id).exists():
            return 409, {"detail": "This package contains no events yet; tickets cannot be sold."}

        current = Ticket.select(fn.COUNT(Ticket.code)).where(field == target_id).scalar() or 0
        if current >= target.total_seats:
            return 409, {
                "detail": f"No more available seats for this {label}.",
                "current_tickets": current,
                "total_seats": target.total_seats,
            }
        return None

    # ---------- queries ----------

    @staticmethod
    def list_tickets(
        page: int,
        per_page: int,
        event_id: Optional[int] = None,
        package_id: Optional[int] = None,
        *,
        p: Optional[Principal] = None,
    ) -> Tuple[List[TicketItem], int]:
        owner_id: Optional[int] = None
        if p is not None and not TicketsService._is_admin(p):
            owner_id = TicketsService._principal_user_id(p)

        items, total = TicketsRepository.list_tickets(
            page=page,
            per_page=per_page,
            event_id=event_id,
            package_id=package_id,
            owner_id=owner_id,
        )
        return [TicketsService.build_ticket_item(t) for t in items], total

    @staticmethod
    def get_ticket(code: str) -> Optional[TicketOut]:
        t = TicketsRepository.get_by_code(code)
        if not t:
            return None
        return TicketsService.build_ticket_out(t)

    # ---------- commands ----------

    @staticmethod
    def create_ticket(data: TicketIn) -> Tuple[int, dict | TicketOut]:
        """POST: server-generated code."""
        if (data.package_id is None) == (data.event_id is None):
            return 422, {"detail": "Exactly one of package_id or event_id must be provided."}

        for _ in range(3):
            code = uuid.uuid4().hex[:10].upper()
            status, res = TicketsService.upsert_ticket(code, data.event_id, data.package_id)
            if status != 409 or TicketsRepository.get_by_code(code) is None:
                return (201 if status in (201, 204) else status), res
        return 409, {"detail": "Could not generate a unique ticket code, please retry."}

    @staticmethod
    def upsert_ticket(
        code: str,
        event_id: Optional[int],
        package_id: Optional[int],
    ) -> Tuple[int, dict | TicketOut]:
        """
        PUT semantics (client-controlled key):
          201 – new ticket sold
          204 – identical ticket already exists (idempotent)
          409 – code exists for another target / no seats left
          404 – target not found
        """
        if (package_id is None) == (event_id is None):
            return 422, {"detail": "Exactly one of package_id or event_id must be provided."}

        existing = TicketsRepository.get_by_code(code)
        if existing:
            if existing.event_id == event_id and existing.package_id == package_id:
                return 204, TicketsService.build_ticket_out(existing)
            return 409, {"detail": "Ticket code already used for another event/package."}

        try:
            with db.atomic():
                err = TicketsService._capacity_error(event_id, package_id)
                if err:
                    return err
                t = TicketsRepository.create(
                    {"code": code, "event": event_id, "package": package_id}
                )
        except IntegrityError:
            return 409, {"detail": "Ticket code already exists."}

        return 201, TicketsService.build_ticket_out(t)

    @staticmethod
    def delete_ticket(code: str) -> Tuple[int, Optional[dict]]:
        deleted = TicketsRepository.delete(code)
        if deleted:
            return 204, None
        return 404, {"detail": "Ticket not found"}
