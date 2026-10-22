import uuid
from typing import Optional, List

from fastapi import HTTPException

from app.repositories.clients_repo import ClientsRepository
from app.dtos.clients_schemas import (
    ClientIn,
    ClientUpdate,
    ClientTicketDetailsResponse,
    PublicClientOut,
)
from app.integrations.data_service_client import data_client


def _not_found(what: str = "Client not found"):
    return HTTPException(status_code=404, detail=what)


class ClientsService:

    # ------------------------------------------------------------ CRUD

    @staticmethod
    def create_client(data: ClientIn) -> dict:
        email = str(data.email).lower()
        if ClientsRepository.get_client_by_email(email):
            raise HTTPException(status_code=409, detail="Client already exists")
        # optional fields are stored only when present (document DB, Lab 3)
        doc = data.model_dump(exclude_none=True)
        doc["email"] = email
        doc["tickets"] = []
        return ClientsRepository.create_client(doc)

    @staticmethod
    def ensure_client_document(email: str) -> dict:
        """Used when the admin creates an IDM user with role `client`."""
        existing = ClientsRepository.get_client_by_email(email)
        if existing:
            return existing
        return ClientsRepository.create_client({"email": email.lower(), "tickets": []})

    @staticmethod
    def get_client(client_id: str) -> dict:
        client = ClientsRepository.get_client_by_id(client_id)
        if not client:
            raise _not_found()
        return client

    @staticmethod
    def get_client_by_email(email: str) -> dict:
        client = ClientsRepository.get_client_by_email(email)
        if not client:
            raise _not_found("No client profile for this user yet; create it with POST /api/clients")
        return client

    @staticmethod
    def update_client(client_id: str, data: ClientUpdate) -> dict:
        ClientsService.get_client(client_id)
        # only the fields sent by the caller; email and tickets are never touched
        payload = data.model_dump(exclude_unset=True)
        return ClientsRepository.update_client(client_id, payload)

    @staticmethod
    def delete_client(client_id: str) -> None:
        if not ClientsRepository.delete_client(client_id):
            raise _not_found()

    @staticmethod
    def list_clients(page: int, per_page: int, email: Optional[str] = None):
        return ClientsRepository.list_clients(page, per_page, email)

    # ------------------------------------------------------------ tickets

    @staticmethod
    def add_ticket_to_client(client_id: str, ticket: dict, token: str) -> dict:
        """
        Buy a ticket: chain call Client WebService -> Event WebService
        (PUT /api/event-manager/tickets/{code}). A client may buy several
        tickets for the same event/package (Lab 1, 1.1).
        """
        ClientsService.get_client(client_id)

        event_id = ticket.get("event_id")
        package_id = ticket.get("package_id")
        code = uuid.uuid4().hex

        response = data_client.create_ticket(code, event_id, package_id, token)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Event or package not found")
        if response.status_code in (401, 403):
            raise HTTPException(status_code=response.status_code, detail="Not allowed to buy this ticket")
        if response.status_code == 409:
            try:
                detail = response.json().get("detail")
            except Exception:
                detail = None
            raise HTTPException(status_code=409, detail=detail or "Ticket cannot be sold")
        if response.status_code not in (200, 201, 204):
            raise HTTPException(status_code=502, detail="Upstream data service error")

        ticket_doc = {"code": code, "event_id": event_id, "package_id": package_id}
        if event_id is not None:
            event = data_client.get_event(event_id, token) or {}
            ticket_doc["event_name"] = event.get("name")
            ticket_doc["location"] = event.get("location")
        else:
            package = data_client.get_package(package_id, token) or {}
            ticket_doc["event_name"] = package.get("name")
            ticket_doc["location"] = package.get("location")
            ticket_doc["events"] = [
                {"id": e.get("id"), "name": e.get("name"), "location": e.get("location")}
                for e in data_client.get_package_events(package_id, token)
            ]

        return ClientsRepository.add_ticket(client_id, ticket_doc)

    @staticmethod
    def validate_client_ticket(client: dict, ticket_code: str, token: str) -> ClientTicketDetailsResponse:
        """
        Chain call: the ticket must exist in the client document *and* in Event
        WebService; the event/package the ticket was issued for is returned too.
        """
        client_id = str(client["_id"])
        entry = next((t for t in client.get("tickets") or [] if t.get("code") == ticket_code), None)
        if not entry:
            raise _not_found("Ticket not found for client")

        remote, status = data_client.get_ticket(ticket_code, token)
        if status in (401, 403):
            raise HTTPException(status_code=status, detail="Not allowed to see this ticket")
        if status == 404:
            return ClientTicketDetailsResponse(
                client_id=client_id,
                client_email=client.get("email"),
                ticket_code=ticket_code,
                is_valid=False,
            )
        if status != 200 or not remote:
            raise HTTPException(status_code=502, detail="Upstream data service error")

        event = data_client.get_event(remote["event_id"], token) if remote.get("event_id") else None
        package = data_client.get_package(remote["package_id"], token) if remote.get("package_id") else None

        return ClientTicketDetailsResponse(
            client_id=client_id,
            client_email=client.get("email"),
            ticket_code=ticket_code,
            is_valid=True,
            event=event,
            package=package,
        )

    # ------------------------------------------------------------ owner-event view

    @staticmethod
    def list_buyers(token: str, event_id: Optional[int] = None, package_id: Optional[int] = None) -> List[PublicClientOut]:
        """
        Buyers of the caller's events/packages, with public data only
        (Lab 1, 1.4 and interaction (5) from the component diagram).
        """
        try:
            owned = data_client.list_owner_ticket_codes(token, event_id, package_id)
        except Exception:
            raise HTTPException(status_code=502, detail="Upstream data service error")
        codes = {t["code"] for t in owned}

        result: List[PublicClientOut] = []
        for c in ClientsRepository.find_by_ticket_codes(list(codes)):
            social = c.get("social") or {}
            result.append(
                PublicClientOut(
                    id=str(c["_id"]),
                    first_name=c.get("first_name") if c.get("public_name") else None,
                    last_name=c.get("last_name") if c.get("public_name") else None,
                    social=social if social.get("public_social") else None,
                    tickets=[t for t in c.get("tickets") or [] if t.get("code") in codes],
                )
            )
        return result
