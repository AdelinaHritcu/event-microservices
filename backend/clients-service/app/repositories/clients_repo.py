from typing import Optional, List

from bson import ObjectId
from bson.errors import InvalidId

from app.database.mongo_connection import clients_collection as col


def _oid(client_id: str) -> Optional[ObjectId]:
    try:
        return ObjectId(client_id)
    except (InvalidId, TypeError):
        return None


class ClientsRepository:

    @staticmethod
    def create_client(doc: dict) -> dict:
        result = col.insert_one(doc)
        return col.find_one({"_id": result.inserted_id})

    @staticmethod
    def get_client_by_email(email: str) -> Optional[dict]:
        return col.find_one({"email": email.lower()})

    @staticmethod
    def get_client_by_id(client_id: str) -> Optional[dict]:
        oid = _oid(client_id)
        return col.find_one({"_id": oid}) if oid else None

    @staticmethod
    def update_client(client_id: str, data: dict) -> Optional[dict]:
        oid = _oid(client_id)
        if not oid:
            return None
        if data:
            col.update_one({"_id": oid}, {"$set": data})
        return col.find_one({"_id": oid})

    @staticmethod
    def delete_client(client_id: str) -> bool:
        oid = _oid(client_id)
        return bool(oid) and col.delete_one({"_id": oid}).deleted_count > 0

    @staticmethod
    def delete_client_by_email(email: str) -> bool:
        return col.delete_one({"email": email.lower()}).deleted_count > 0

    @staticmethod
    def add_ticket(client_id: str, ticket: dict) -> Optional[dict]:
        oid = _oid(client_id)
        if not oid:
            return None
        col.update_one({"_id": oid}, {"$push": {"tickets": ticket}})
        return col.find_one({"_id": oid})

    @staticmethod
    def find_by_ticket_codes(codes: List[str]) -> List[dict]:
        if not codes:
            return []
        return list(col.find({"tickets.code": {"$in": codes}}))

    @staticmethod
    def list_clients(page: int, per_page: int, email: Optional[str] = None):
        q: dict = {}
        if email:
            q["email"] = {"$regex": email, "$options": "i"}
        skip = (page - 1) * per_page
        items = list(col.find(q).skip(skip).limit(per_page))
        total = col.count_documents(q)
        return items, total
