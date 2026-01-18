import uuid
from typing import Optional, Tuple, cast

from pydantic import EmailStr

from app.repositories.clients_repo import ClientsRepository
from app.dtos.clients_schemas import ClientIn, ClientTicketDetailsResponse
from app.integrations.data_service_client import data_client


class ClientsService:

    @staticmethod
    def create_client(data: ClientIn):
        email_str = str(data.email).lower()
        existing = ClientsRepository.get_client_by_email(email_str)
        if existing:
            return None

        payload = data.model_copy()
        payload.email = cast(EmailStr, email_str)

        created = ClientsRepository.create_client(payload)
        return created

    @staticmethod
    def update_client(client_id: str, data: ClientIn):
        existing = ClientsRepository.get_client_by_id(client_id)
        if not existing:
            return None

        payload = data.model_dump()
        payload.pop("email", None)

        updated = ClientsRepository.update_client(client_id, payload)
        return updated

    @staticmethod
    def add_ticket_to_client(
        client_id: str,
        ticket: dict,
    ) -> Tuple[Optional[dict], int, Optional[str]]:
        client = ClientsRepository.get_client_by_id(client_id)
        if not client:
            return None, 404, "Client not found"

        event_id = ticket.get("event_id")
        package_id = ticket.get("package_id")

        if (event_id is None and package_id is None) or (
            event_id is not None and package_id is not None
        ):
            return None, 400, "Provide exactly one between event_id and package_id"

        existing_tickets = client.get("tickets") or []
        for t in existing_tickets:
            if t.get("event_id") == event_id and t.get("package_id") == package_id:
                return None, 409, "Ticket already exists"

        code = uuid.uuid4().hex

        response = data_client.create_ticket(code, event_id, package_id)

        if response.status_code == 404:
            return None, 404, "Event or package not found"
        if response.status_code == 409:
            return None, 409, "Ticket already exists"
        if response.status_code not in (200, 201, 204):
            return None, 502, "Upstream data service error"

        event = None
        package = None

        if event_id is not None:
            event = data_client.get_event(event_id)
        if package_id is not None:
            package = data_client.get_package(package_id)

        ticket_doc = {
            "code": code,
            "event_id": event_id,
            "package_id": package_id,
            "event_name": event.get("name") if event else None,
            "location": event.get("location") if event else None,
        }

        if not ticket_doc["event_name"] and package:
            ticket_doc["event_name"] = package.get("name")
            ticket_doc["location"] = package.get("location")

        ClientsRepository.add_ticket(client_id, ticket_doc)
        updated_client = ClientsRepository.get_client_by_id(client_id)
        return updated_client, 200, None

    @staticmethod
    def get_client(client_id: str):
        return ClientsRepository.get_client_by_id(client_id)

    @staticmethod
    def validate_client_ticket(
        client_id: str,
        ticket_code: str,
    ) -> Tuple[ClientTicketDetailsResponse, int, Optional[str]]:
        client = ClientsRepository.get_client_by_id(client_id)
        if not client:
            return (
                ClientTicketDetailsResponse(
                    client_id=client_id,
                    client_email=None,
                    ticket_code=ticket_code,
                    is_valid=False,
                    event=None,
                    package=None,
                ),
                404,
                "Client not found",
            )

        client_email = client.get("email")
        tickets = client.get("tickets", []) or []
        ticket_entry = next((t for t in tickets if t.get("code") == ticket_code), None)
        if not ticket_entry:
            return (
                ClientTicketDetailsResponse(
                    client_id=client_id,
                    client_email=client_email,
                    ticket_code=ticket_code,
                    is_valid=False,
                    event=None,
                    package=None,
                ),
                404,
                "Ticket not found for client",
            )

        ticket_remote, status = data_client.get_ticket(ticket_code)

        if status == 404:
            return (
                ClientTicketDetailsResponse(
                    client_id=client_id,
                    client_email=client_email,
                    ticket_code=ticket_code,
                    is_valid=False,
                    event=None,
                    package=None,
                ),
                404,
                "Ticket not found",
            )

        if status != 200 or not ticket_remote:
            return (
                ClientTicketDetailsResponse(
                    client_id=client_id,
                    client_email=client_email,
                    ticket_code=ticket_code,
                    is_valid=False,
                    event=None,
                    package=None,
                ),
                502,
                "Upstream data service error",
            )

        event = None
        package = None

        event_id = ticket_remote.get("event_id")
        if event_id is not None:
            event = data_client.get_event(event_id)

        package_id = ticket_remote.get("package_id")
        if package_id is not None:
            package = data_client.get_package(package_id)

        return (
            ClientTicketDetailsResponse(
                client_id=client_id,
                client_email=client_email,
                ticket_code=ticket_code,
                is_valid=True,
                event=event,
                package=package,
            ),
            200,
            None,
        )

    @staticmethod
    def list_clients(page: int, per_page: int):
        return ClientsRepository.list_clients(page, per_page)
