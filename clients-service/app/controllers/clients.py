from typing import Dict

from fastapi import APIRouter, HTTPException, Depends

from app.services.clients_service import ClientsService
from app.dtos.clients_schemas import (
    ClientIn,
    ClientOut,
    ClientTicketDetailsResponse,
    Link,
)
from app.dtos.clients_schemas import AddTicketToClient
from app.security.auth import require_roles, Principal


router = APIRouter(
    prefix="/api/clients",
    tags=["clients"],
    dependencies=[Depends(require_roles("admin", "owner-event"))],
)

BASE = "/api/clients"


def _links(client_id: str) -> Dict[str, Link]:
    return {
        "self": Link(href=f"{BASE}/{client_id}", type="GET"),
        "parent": Link(href=BASE, type="GET"),
        "tickets": Link(href=f"{BASE}/{client_id}/tickets", type="GET"),
    }


@router.post("/", response_model=ClientOut, status_code=201)
def create_client(payload: ClientIn):
    try:
        created = ClientsService.create_client(payload)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not created:
        raise HTTPException(status_code=409, detail="Client already exists")

    client_id = str(created.get("_id"))
    created["_id"] = client_id
    return ClientOut(**created, links=_links(client_id))


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: str, payload: ClientIn):
    try:
        updated = ClientsService.update_client(client_id, payload)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")

    cid = str(updated.get("_id"))
    updated["_id"] = cid
    return ClientOut(**updated, links=_links(cid))


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: str):
    try:
        client = ClientsService.get_client(client_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    cid = str(client.get("_id"))
    client["_id"] = cid
    return ClientOut(**client, links=_links(cid))


@router.post("/{client_id}/tickets", response_model=ClientOut)
def add_ticket_to_client(client_id: str, ticket: AddTicketToClient):
    try:
        updated_client, code, message = ClientsService.add_ticket_to_client(
            client_id,
            ticket.model_dump(),
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if code == 400:
        raise HTTPException(status_code=400, detail=message or "Invalid request")
    if code == 404:
        raise HTTPException(status_code=404, detail=message or "Client or resource not found")
    if code == 409:
        raise HTTPException(status_code=409, detail=message or "Ticket already exists")
    if code == 502:
        raise HTTPException(status_code=502, detail=message or "Upstream data service error")
    if not updated_client:
        raise HTTPException(status_code=500, detail="Unknown ticket creation error")

    cid = str(updated_client.get("_id"))
    updated_client["_id"] = cid
    return ClientOut(**updated_client, links=_links(cid))


@router.get("/{client_id}/tickets/{ticket_code}", response_model=ClientTicketDetailsResponse)
def validate_ticket(client_id: str, ticket_code: str):
    try:
        ticket_info = ClientsService.validate_client_ticket(client_id, ticket_code)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    return ticket_info


@router.get("/", response_model=dict)
def list_clients(page: int = 1, items_per_page: int = 10):
    try:
        clients, total = ClientsService.list_clients(page, items_per_page)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    items = []
    for c in clients:
        client_id = str(c.get("_id"))
        c["_id"] = client_id
        tickets = c.get("tickets") or []
        c["tickets"] = tickets
        items.append(
            ClientOut(
                **c,
                links=_links(client_id),
            )
        )

    return {
        "items": items,
        "page": page,
        "items_per_page": items_per_page,
        "total_items": total,
        "links": {
            "self": Link(href=f"{BASE}?page={page}&items_per_page={items_per_page}", type="GET"),
            "parent": Link(href=BASE, type="GET"),
        },
    }


@router.get("/{client_id}/tickets", response_model=dict)
def list_client_tickets(client_id: str):
    try:
        client = ClientsService.get_client(client_id)
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return {
        "email": client.get("email"),
        "tickets": client.get("tickets", []),
        "links": {
            "self": Link(href=f"{BASE}/{client_id}/tickets", type="GET"),
            "parent": Link(href=f"{BASE}/{client_id}", type="GET"),
        },
    }
