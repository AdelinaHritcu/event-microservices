import os
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.responses import Response

from app.services.clients_service import ClientsService
from app.dtos.clients_schemas import (
    ClientIn,
    ClientUpdate,
    ClientOut,
    ClientListResponse,
    ClientTicketDetailsResponse,
    BuyersResponse,
    Link,
    AddTicketToClient,
)
from app.security.auth import require_roles, Principal, require_self_or_admin, bearer_token

BASE = "/api/clients"
# public URL of Event WebService, used only to build navigation links
EVENTS_PUBLIC_URL = os.getenv("EVENTS_PUBLIC_URL", "http://localhost:8000").rstrip("/")

router = APIRouter(prefix=BASE, tags=["clients"])


def _links(client_id: str) -> Dict[str, Link]:
    return {
        "self": Link(href=f"{BASE}/{client_id}", type="GET"),
        "parent": Link(href=BASE, type="GET"),
        "update": Link(href=f"{BASE}/{client_id}", type="PUT"),
        "tickets": Link(href=f"{BASE}/{client_id}/tickets", type="GET"),
        "buy-ticket": Link(href=f"{BASE}/{client_id}/tickets", type="POST"),
        "events": Link(href=f"{EVENTS_PUBLIC_URL}/api/event-manager/events", type="GET"),
        "event-packets": Link(href=f"{EVENTS_PUBLIC_URL}/api/event-manager/event-packets", type="GET"),
    }


def _out(doc: dict) -> ClientOut:
    cid = str(doc.get("_id"))
    data = {**doc, "_id": cid, "tickets": doc.get("tickets") or []}
    return ClientOut(**data, links=_links(cid))


def _load_for(client_id: str, p: Principal) -> dict:
    doc = ClientsService.get_client(client_id)
    require_self_or_admin(doc, p)
    return doc


def _tickets_body(doc: dict) -> dict:
    cid = str(doc["_id"])
    return {
        "client_id": cid,
        "email": doc.get("email"),
        "items": doc.get("tickets") or [],
        "_links": {
            "self": {"href": f"{BASE}/{cid}/tickets", "type": "GET"},
            "parent": {"href": f"{BASE}/{cid}", "type": "GET"},
            "buy-ticket": {"href": f"{BASE}/{cid}/tickets", "type": "POST"},
        },
    }


# ------------------------------------------------------------ collection

@router.get("", response_model=ClientListResponse)
def list_clients(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
    email: Optional[str] = Query(None, description="Partial match on email"),
    p: Principal = Depends(require_roles("admin")),
):
    docs, total = ClientsService.list_clients(page, items_per_page, email)
    q = f"&email={email}" if email else ""
    links = {
        "self": Link(href=f"{BASE}?page={page}&items_per_page={items_per_page}{q}", type="GET"),
        "parent": Link(href="/", type="GET"),
    }
    if page * items_per_page < total:
        links["next"] = Link(href=f"{BASE}?page={page + 1}&items_per_page={items_per_page}{q}", type="GET")
    if page > 1:
        links["prev"] = Link(href=f"{BASE}?page={page - 1}&items_per_page={items_per_page}{q}", type="GET")
    return ClientListResponse(
        items=[_out(d) for d in docs],
        page=page,
        items_per_page=items_per_page,
        total_items=total,
        links=links,
    )


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def create_client(
    payload: ClientIn,
    p: Principal = Depends(require_roles("admin", "client")),
):
    """The admin creates any profile; a client may create only its own (same email as the token)."""
    if p.role == "client" and str(payload.email).lower() != p.email:
        raise HTTPException(status_code=403, detail="A client can create only its own profile")
    return _out(ClientsService.create_client(payload))


# ------------------------------------------------------------ current client

@router.get("/me", response_model=ClientOut)
def get_me(p: Principal = Depends(require_roles("client"))):
    return _out(ClientsService.get_client_by_email(p.email))


@router.put("/me", status_code=status.HTTP_204_NO_CONTENT)
def update_me(payload: ClientUpdate, p: Principal = Depends(require_roles("client"))):
    doc = ClientsService.get_client_by_email(p.email)
    ClientsService.update_client(str(doc["_id"]), payload)
    # Lab 2: PUT that replaces an existing resource -> 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me/tickets")
def list_my_tickets(p: Principal = Depends(require_roles("client"))):
    return _tickets_body(ClientsService.get_client_by_email(p.email))


@router.post("/me/tickets", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def buy_my_ticket(
    ticket: AddTicketToClient,
    p: Principal = Depends(require_roles("client")),
    token: str = Depends(bearer_token),
):
    doc = ClientsService.get_client_by_email(p.email)
    return _out(ClientsService.add_ticket_to_client(str(doc["_id"]), ticket.model_dump(), token))


# ------------------------------------------------------------ owner-event

@router.get("/buyers", response_model=BuyersResponse)
def list_buyers(
    event_id: Optional[int] = Query(None, ge=1),
    package_id: Optional[int] = Query(None, ge=1),
    p: Principal = Depends(require_roles("owner-event")),
    token: str = Depends(bearer_token),
):
    """Public data of the clients who bought tickets for the caller's events/packages."""
    items = ClientsService.list_buyers(token, event_id, package_id)
    return BuyersResponse(
        items=items,
        total_items=len(items),
        links={
            "self": Link(href=f"{BASE}/buyers", type="GET"),
            "parent": Link(href=BASE, type="GET"),
        },
    )


# ------------------------------------------------------------ single client

@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: str, p: Principal = Depends(require_roles("admin", "client"))):
    return _out(_load_for(client_id, p))


@router.put("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_client(
    client_id: str,
    payload: ClientUpdate,
    p: Principal = Depends(require_roles("admin", "client")),
):
    _load_for(client_id, p)
    ClientsService.update_client(client_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: str, p: Principal = Depends(require_roles("admin"))):
    ClientsService.delete_client(client_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{client_id}/tickets")
def list_client_tickets(client_id: str, p: Principal = Depends(require_roles("client"))):
    return _tickets_body(_load_for(client_id, p))


@router.post("/{client_id}/tickets", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
def add_ticket_to_client(
    client_id: str,
    ticket: AddTicketToClient,
    p: Principal = Depends(require_roles("client")),
    token: str = Depends(bearer_token),
):
    _load_for(client_id, p)
    return _out(ClientsService.add_ticket_to_client(client_id, ticket.model_dump(), token))


@router.get("/{client_id}/tickets/{ticket_code}", response_model=ClientTicketDetailsResponse)
def validate_ticket(
    client_id: str,
    ticket_code: str,
    p: Principal = Depends(require_roles("client", "owner-event")),
    token: str = Depends(bearer_token),
):
    """
    Validates a ticket and returns the event/package it was issued for.
    - client: only its own tickets;
    - owner-event: Event WebService checks that the ticket belongs to one of its events.
    """
    doc = ClientsService.get_client(client_id)
    if p.role == "client":
        require_self_or_admin(doc, p)
    res = ClientsService.validate_client_ticket(doc, ticket_code, token)
    res.links = {
        "self": Link(href=f"{BASE}/{client_id}/tickets/{ticket_code}", type="GET"),
        "parent": Link(href=f"{BASE}/{client_id}/tickets", type="GET"),
    }
    return res
