from typing import List, Tuple, Optional

import logging
import requests
from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import PyMongoError

from app.database.mongo import clients_collection
from app.dtos.clients_schemas import (
    ClientIn,
    ClientOut,
    TicketRef,
    TicketValidationRequest,
    TicketValidationResponse,
)

logger = logging.getLogger(__name__)

EVENT_WS_URL = "http://127.0.0.1:8000/api/event-manager"


def _normalize_tickets(doc: dict) -> List[TicketRef]:
    raw = doc.get("tickets")
    if not isinstance(raw, list):
        raw = []

    result: List[TicketRef] = []
    for item in raw:
        if isinstance(item, dict):
            try:
                result.append(TicketRef(**item))
            except Exception as e:
                logger.warning("Cannot build TicketRef from %r: %r", item, e)
        else:
            logger.warning("Unknown ticket format: %r", item)
    return result


def _to_out(doc: dict) -> ClientOut:
    return ClientOut(
        id=str(doc["_id"]),
        email=doc["email"],
        first_name=doc.get("first_name"),
        last_name=doc.get("last_name"),
        is_name_public=doc.get("is_name_public", True),
        social_links=doc.get("social_links"),
        tickets=_normalize_tickets(doc),
    )


def _find_client_doc(client_id: str) -> Optional[dict]:
    try:
        oid = ObjectId(client_id)
    except InvalidId:
        logger.warning("Invalid client id: %r", client_id)
        return None

    try:
        return clients_collection.find_one({"_id": oid})
    except PyMongoError as e:
        logger.error("ERROR in _find_client_doc: %r", e)
        return None


def list_clients(page: int, per_page: int) -> Tuple[List[ClientOut], int]:
    skip = (page - 1) * per_page
    try:
        cursor = clients_collection.find().skip(skip).limit(per_page)
        docs = list(cursor)
        total = clients_collection.count_documents({})
    except PyMongoError as e:
        logger.error("ERROR in list_clients: %r", e)
        return [], 0

    return [_to_out(d) for d in docs], total


def create_client(payload: ClientIn) -> ClientOut:
    try:
        existing = clients_collection.find_one({"email": payload.email})
    except PyMongoError as e:
        logger.error("ERROR in create_client / find_one: %r", e)
        raise

    if existing:
        raise ValueError("Client already exists")

    doc = payload.model_dump(exclude_none=True)

    tickets = doc.get("tickets")
    if not isinstance(tickets, list):
        doc["tickets"] = []

    try:
        result = clients_collection.insert_one(doc)
    except PyMongoError as e:
        logger.error("ERROR in create_client / insert_one: %r", e)
        raise

    doc["_id"] = result.inserted_id
    return _to_out(doc)


def get_client(client_id: str) -> Optional[ClientOut]:
    doc = _find_client_doc(client_id)
    if not doc:
        return None
    return _to_out(doc)


def update_client(client_id: str, payload: ClientIn) -> Optional[ClientOut]:
    update_doc = payload.model_dump(exclude_none=True)

    try:
        result = clients_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": update_doc},
        )
    except (PyMongoError, InvalidId) as e:
        logger.error("ERROR in update_client / update_one: %r", e)
        return None

    if result.matched_count == 0:
        return None

    return get_client(client_id)


def delete_client(client_id: str) -> bool:
    try:
        r = clients_collection.delete_one({"_id": ObjectId(client_id)})
        return r.deleted_count == 1
    except (PyMongoError, InvalidId) as e:
        logger.error("ERROR in delete_client: %r", e)
        return False


def validate_ticket_for_client(
    client_id: str,
    req: TicketValidationRequest,
) -> Optional[TicketValidationResponse]:

    doc = _find_client_doc(client_id)
    if not doc:
        return None

    ticket_code = req.ticket_code
    url = f"{EVENT_WS_URL}/tickets/{ticket_code}"

    try:
        resp = requests.get(url, timeout=2)
    except Exception as e:
        logger.error("ERROR calling Event WS: %r", e)
        return TicketValidationResponse(
            valid=False,
            reason="Event service unreachable",
        )

    if resp.status_code == 404:
        return TicketValidationResponse(valid=False, reason="Ticket not found")

    if resp.status_code != 200:
        logger.warning("Event WS returned %s for ticket %s", resp.status_code, ticket_code)
        return TicketValidationResponse(
            valid=False,
            reason=f"Event service error {resp.status_code}",
        )

    data = resp.json()

    ticket_ref = TicketRef(
        ticket_code=ticket_code,
        mode="long",
        event_name=data.get("event_name"),
        event_location=data.get("location"),
        package_name=data.get("package_name"),
    )

    try:
        clients_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$addToSet": {"tickets": ticket_ref.model_dump()}},
        )
    except (PyMongoError, InvalidId) as e:
        logger.error("ERROR in validate_ticket_for_client / update_one: %r", e)

    return TicketValidationResponse(
        valid=True,
        event_name=ticket_ref.event_name,
        event_location=ticket_ref.event_location,
        package_name=ticket_ref.package_name,
    )
