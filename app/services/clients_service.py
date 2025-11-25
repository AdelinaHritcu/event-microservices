from app.repositories.clients_repo import ClientsRepository
from app.repositories.tickets_repo import TicketsRepository
from app.repositories.events_repo import EventsRepository
from app.repositories.packages_repo import PackagesRepository

from app.dtos.clients_schemas import (
    ClientIn,
    ClientTicketDetailsResponse,
)


class ClientsService:

    @staticmethod
    def create_client(data: ClientIn):
        email = str(data.email)
        existing = ClientsRepository.get_client_by_email(email)
        if existing:
            return None
        ClientsRepository.create_client(data)
        return ClientsRepository.get_client_by_email(email)

    @staticmethod
    def update_client(email: str, data: ClientIn):
        email_str = str(email)
        existing = ClientsRepository.get_client_by_email(email_str)
        if not existing:
            return None
        payload = data.model_dump()
        payload["email"] = email_str
        ClientsRepository.update_client(email_str, payload)
        return ClientsRepository.get_client_by_email(email_str)

    @staticmethod
    def add_ticket_to_client(email: str, ticket: dict):
        code = ticket.get("code")
        if not code:
            return None

        db_ticket = TicketsRepository.get_by_code(code)
        if not db_ticket:
            return None

        ticket_doc = {
            "code": db_ticket.code,
            "event_id": getattr(db_ticket, "event_id", None),
            "package_id": getattr(db_ticket, "package_id", None),
            "name": None,
            "location": None,
        }

        if getattr(db_ticket, "event_id", None):
            event = EventsRepository.get_by_id(db_ticket.event)
            if event:
                ticket_doc["name"] = event.name
                ticket_doc["location"] = event.location

        return ClientsRepository.add_ticket(email, ticket_doc)

    @staticmethod
    def get_client(email: str):
        return ClientsRepository.get_client_by_email(str(email))

    @staticmethod
    def validate_client_ticket(email: str, ticket_code: str) -> ClientTicketDetailsResponse:
        email_str = str(email)

        client = ClientsRepository.get_client_by_email(email_str)
        if not client:
            return ClientTicketDetailsResponse(
                client_email=email_str,
                ticket_code=ticket_code,
                is_valid=False,
                event=None,
                package=None,
            )

        tickets = client.get("tickets", []) or []
        ticket_entry = next((t for t in tickets if t.get("code") == ticket_code), None)
        if not ticket_entry:
            return ClientTicketDetailsResponse(
                client_email=email_str,
                ticket_code=ticket_code,
                is_valid=False,
                event=None,
                package=None,
            )

        ticket = TicketsRepository.get_by_code(ticket_code)
        if not ticket:
            return ClientTicketDetailsResponse(
                client_email=email_str,
                ticket_code=ticket_code,
                is_valid=False,
                event=None,
                package=None,
            )

        event = None
        if getattr(ticket, "event_id", None):
            event = EventsRepository.get_by_id(ticket.event)

        package = None
        if getattr(ticket, "package_id", None):
            package = PackagesRepository.get_by_id(ticket.package)

        return ClientTicketDetailsResponse(
            client_email=email_str,
            ticket_code=ticket_code,
            is_valid=True,
            event=event,
            package=package,
        )

    @staticmethod
    def list_clients(page: int, per_page: int):
        return ClientsRepository.list_clients(page, per_page)

