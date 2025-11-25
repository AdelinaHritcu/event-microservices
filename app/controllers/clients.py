from fastapi import APIRouter, HTTPException
from typing import Dict

from app.services.clients_service import ClientsService
from app.dtos.clients_schemas import (
    ClientIn,
    ClientOut,
    ClientTicketDetailsResponse,
    Link
)
from app.dtos.tickets_schemas import AddTicketToClient


router = APIRouter(
    prefix="/api/event-manager/clients",
    tags=["Clients"],
)

BASE = "/api/event-manager/clients"


def _links(email: str) -> Dict[str, Link]:
    return {
        "self": Link(href=f"{BASE}/{email}", type="GET"),
        "parent": Link(href=BASE, type="GET"),
        "tickets": Link(href=f"{BASE}/{email}/tickets", type="GET"),
    }


@router.post("/", response_model=ClientOut, status_code=201)
def create_client(payload: ClientIn):
    created = ClientsService.create_client(payload)
    if not created:
        raise HTTPException(status_code=409, detail="Client already exists")
    email = created["email"]
    return ClientOut(**created, links=_links(email))


@router.put("/{email}", response_model=ClientOut)
def update_client(email: str, payload: ClientIn):
    updated = ClientsService.update_client(email, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientOut(**updated, links=_links(email))


@router.get("/{email}", response_model=ClientOut)
def get_client(email: str):
    client = ClientsService.get_client(email)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientOut(**client, links=_links(email))


@router.post("/{email}/tickets", response_model=ClientOut)
def add_ticket_to_client(email: str, ticket: AddTicketToClient):
    updated = ClientsService.add_ticket_to_client(email, ticket.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")
    return ClientOut(**updated, links=_links(email))


@router.get("/{email}/tickets/{ticket_code}", response_model=ClientTicketDetailsResponse)
def validate_ticket(email: str, ticket_code: str):
    ticket_info, error = ClientsService.validate_client_ticket(email, ticket_code)
    if ticket_info is None:
        return ClientTicketDetailsResponse(
            client_email=email,
            ticket_code=ticket_code,
            is_valid=False,
            event=None,
            package=None
        )
    return ticket_info


@router.get("/", response_model=dict)
def list_clients(page: int = 1, items_per_page: int = 10):
    clients, total = ClientsService.list_clients(page, items_per_page)

    items = []
    for c in clients:
        items.append(
            ClientOut(
                **c,
                links=_links(c["email"])
            )
        )

    return {
        "items": items,
        "page": page,
        "items_per_page": items_per_page,
        "total_items": total,
        "links": {
            "self": Link(href=f"{BASE}?page={page}&items_per_page={items_per_page}", type="GET"),
            "parent": Link(href=BASE, type="GET")
        }
    }

@router.get("/{email}/tickets", response_model=dict)
def list_client_tickets(email: str):
    client = ClientsService.get_client(email)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "email": email,
        "tickets": client.get("tickets", []),
        "links": {
            "self": Link(href=f"{BASE}/{email}/tickets", type="GET"),
            "parent": Link(href=f"{BASE}/{email}", type="GET")
        }
    }
