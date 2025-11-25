from app.database.mongo_connection import db, clients_collection
from app.dtos.clients_schemas import ClientIn
from bson import ObjectId


class ClientsRepository:

    @staticmethod
    def create_client(data: ClientIn):
        client_dict = data.model_dump(by_alias=True)
        result = db.clients.insert_one(client_dict)
        return db.clients.find_one({"_id": result.inserted_id})

    @staticmethod
    def get_client_by_email(email: str):
        return db.clients.find_one({"email": email})

    @staticmethod
    def update_client(email: str, data: dict):
        db.clients.update_one({"email": email}, {"$set": data})
        return db.clients.find_one({"email": email})

    @staticmethod
    def add_ticket(email: str, ticket: dict):
        db.clients.update_one(
            {"email": email},
            {"$push": {"tickets": ticket}}
        )
        return db.clients.find_one({"email": email})

    @staticmethod
    def count_clients():
        return db.clients.count_documents({})

    @staticmethod
    def list_clients(page: int, per_page: int):
        skip = (page - 1) * per_page
        cursor = clients_collection.find().skip(skip).limit(per_page)

        clients = list(cursor)
        total = clients_collection.count_documents({})
        return clients, total
