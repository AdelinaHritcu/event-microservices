from typing import List

from fastapi import APIRouter, HTTPException, Query
from bson import ObjectId
from pymongo.errors import PyMongoError

from app.database.mongo import clients_collection
from app.dtos.clients_schemas import (
    ClientIn,
    ClientOut,
    TicketRef,
    TicketValidationRequest,
    TicketValidationResponse,
)

router = APIRouter(
    prefix="/api/event-manager/clients",
    tags=["clients"],
)


def _doc_to_out(doc: dict) -> ClientOut:
    raw_tickets = doc.get("tickets")
    if not isinstance(raw_tickets, list):
        raw_tickets = []

    tickets: List[TicketRef] = []
    for item in raw_tickets:
        if isinstance(item, dict):
            try:
                tickets.append(TicketRef(**item))
            except Exception as e:
                print("WARN bad ticket in client doc:", item, repr(e))

    return ClientOut(
        id=str(doc["_id"]),
        email=doc["email"],
        first_name=doc.get("first_name"),
        last_name=doc.get("last_name"),
        is_name_public=doc.get("is_name_public", True),
        social_links=doc.get("social_links"),
        tickets=tickets,
    )


@router.get("", response_model=list[ClientOut])
def list_clients(
    page: int = Query(1, ge=1),
    items_per_page: int = Query(10, ge=1, le=100),
):
    skip = (page - 1) * items_per_page
    try:
        docs = list(
            clients_collection.find().skip(skip).limit(items_per_page)
        )
    except PyMongoError as e:
        print("ERROR list_clients:", repr(e))
        return []

    return [_doc_to_out(d) for d in docs]


@router.post("", response_model=ClientOut, status_code=201)
def create_client(payload: ClientIn):
    try:
        existing = clients_collection.find_one({"email": payload.email})
    except PyMongoError as e:
        print("ERROR create_client/find_one:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    if existing:
        raise HTTPException(status_code=400, detail="Client already exists")

    doc = payload.model_dump(exclude_none=True)
    if not isinstance(doc.get("tickets"), list):
        doc["tickets"] = []

    try:
        result = clients_collection.insert_one(doc)
    except PyMongoError as e:
        print("ERROR create_client/insert_one:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    doc["_id"] = result.inserted_id
    return _doc_to_out(doc)


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: str):
    try:
        doc = clients_collection.find_one({"_id": ObjectId(client_id)})
    except PyMongoError as e:
        print("ERROR get_client:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    if not doc:
        raise HTTPException(status_code=404, detail="Client not found")

    return _doc_to_out(doc)


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: str, payload: ClientIn):
    update_doc = payload.model_dump(exclude_none=True)

    try:
        result = clients_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": update_doc},
        )
    except PyMongoError as e:
        print("ERROR update_client/update_one:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")

    try:
        doc = clients_collection.find_one({"_id": ObjectId(client_id)})
    except PyMongoError as e:
        print("ERROR update_client/find_one:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    return _doc_to_out(doc)


@router.delete("/{client_id}", status_code=204)
def delete_client(client_id: str):
    try:
        result = clients_collection.delete_one({"_id": ObjectId(client_id)})
    except PyMongoError as e:
        print("ERROR delete_client:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")


@router.post(
    "/{client_id}/tickets/validate",
    response_model=TicketValidationResponse,
)
def validate_ticket(client_id: str, payload: TicketValidationRequest):
    try:
        doc = clients_collection.find_one({"_id": ObjectId(client_id)})
    except PyMongoError as e:
        print("ERROR validate_ticket/find_one:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    if not doc:
        raise HTTPException(status_code=404, detail="Client not found")

    ticket_ref = TicketRef(
        ticket_code=payload.ticket_code,
        mode="short",
        event_name=None,
        event_location=None,
        package_name=None,
    )

    try:
        clients_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$addToSet": {"tickets": ticket_ref.model_dump()}},
        )
    except PyMongoError as e:
        print("ERROR validate_ticket/update_one:", repr(e))
        raise HTTPException(status_code=500, detail="Database error")

    return TicketValidationResponse(
        valid=True,
        event_name=None,
        event_location=None,
        package_name=None,
        reason=None,
    )
