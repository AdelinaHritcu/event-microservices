from typing import Dict

from fastapi import APIRouter, HTTPException, Depends

from app.services.clients_service import ClientsService
from app.dtos.clients_schemas import (
    ClientIn,
    ClientOut,
    ClientTicketDetailsResponse,
    Link,
    AddTicketToClient,
)
from app.security.auth import require_roles, Principal, require_self_or_admin, bearer_token

router = APIRouter(
    prefix="/api/clients",
    tags=["clients"],
)

BASE = "/api/clients"


def _links(client_id: str) -> Dict[str, Link]:
    return {
        "self": Link(href=f"{BASE}/{client_id}", type="GET"),
        "parent": Link(href=BASE, type="GET"),
        "tickets": Link(href=f"{BASE}/{client_id}/tickets", type="GET"),
    }


@router.post("/", response_model=ClientOut, status_code=201)
def create_client(
    payload: ClientIn,
    p: Principal = Depends(require_roles("admin")),
):
    try:
        created = ClientsService.create_client(payload)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not created:
        raise HTTPException(status_code=409, detail="Client already exists")

    client_id = str(created.get("_id"))
    created["_id"] = client_id
    return ClientOut(**created, links=_links(client_id))


@router.put("/{client_id}", response_model=ClientOut)
def update_client(
    client_id: str,
    payload: ClientIn,
    p: Principal = Depends(require_roles("admin", "client")),
):
    require_self_or_admin(client_id, p)

    try:
        updated = ClientsService.update_client(client_id, payload)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not updated:
        raise HTTPException(status_code=404, detail="Client not found")

    cid = str(updated.get("_id"))
    updated["_id"] = cid
    return ClientOut(**updated, links=_links(cid))


@router.get("/{client_id}", response_model=ClientOut)
def get_client(
    client_id: str,
    p: Principal = Depends(require_roles("admin", "client")),
):
    require_self_or_admin(client_id, p)

    try:
        client = ClientsService.get_client(client_id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    cid = str(client.get("_id"))
    client["_id"] = cid
    return ClientOut(**client, links=_links(cid))


@router.post("/{client_id}/tickets", response_model=ClientOut)
def add_ticket_to_client(
    client_id: str,
    ticket: AddTicketToClient,
    p: Principal = Depends(require_roles("admin", "client")),
    token: str = Depends(bearer_token),
):
    require_self_or_admin(client_id, p)

    try:
        updated_client, code, message = ClientsService.add_ticket_to_client(
            client_id,
            ticket.model_dump(),
            token,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if code != 200:
        raise HTTPException(status_code=code, detail=message or "Ticket operation failed")

    cid = str(updated_client.get("_id"))
    updated_client["_id"] = cid
    return ClientOut(**updated_client, links=_links(cid))


@router.get("/{client_id}/tickets/{ticket_code}", response_model=ClientTicketDetailsResponse)
def validate_ticket(
    client_id: str,
    ticket_code: str,
    p: Principal = Depends(require_roles("admin", "owner-event")),
    token: str = Depends(bearer_token),
):
    try:
        payload, code, message = ClientsService.validate_client_ticket(
            client_id,
            ticket_code,
            token,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if code != 200:
        raise HTTPException(status_code=code, detail=message or "Ticket validation failed")

    return payload


@router.get("/", response_model=dict)
def list_clients(
    page: int = 1,
    items_per_page: int = 10,
    p: Principal = Depends(require_roles("admin")),
):
    try:
        clients, total = ClientsService.list_clients(page, items_per_page)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    items = []
    for c in clients:
        client_id = str(c.get("_id"))
        c["_id"] = client_id
        c["tickets"] = c.get("tickets") or []
        items.append(ClientOut(**c, links=_links(client_id)))

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
def list_client_tickets(
    client_id: str,
    p: Principal = Depends(require_roles("admin", "client")),
):
    require_self_or_admin(client_id, p)

    try:
        client = ClientsService.get_client(client_id)
    except HTTPException:
        raise
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
