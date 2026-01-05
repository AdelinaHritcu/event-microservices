from app.database.mongo_connection import db


class ClientsRepository:

    @staticmethod
    def create_client(data):
        client_dict = data.model_dump(by_alias=True)
        result = db.clients.insert_one(client_dict)
        return db.clients.find_one({"_id": result.inserted_id})

    @staticmethod
    def get_client_by_email(email: str):
        return db.clients.find_one({"email": email})

    @staticmethod
    def get_client_by_id(client_id: str):
        from bson import ObjectId

        return db.clients.find_one({"_id": ObjectId(client_id)})

    @staticmethod
    def update_client(client_id: str, data: dict):
        from bson import ObjectId

        db.clients.update_one({"_id": ObjectId(client_id)}, {"$set": data})
        return db.clients.find_one({"_id": ObjectId(client_id)})

    @staticmethod
    def add_ticket(client_id: str, ticket: dict):
        from bson import ObjectId

        db.clients.update_one(
            {"_id": ObjectId(client_id)},
            {"$push": {"tickets": ticket}},
        )
        return db.clients.find_one({"_id": ObjectId(client_id)})

    @staticmethod
    def count_clients():
        return db.clients.count_documents({})

    @staticmethod
    def list_clients(page: int, per_page: int):
        skip = (page - 1) * per_page
        cursor = db.clients.find().skip(skip).limit(per_page)
        items = list(cursor)
        total = db.clients.count_documents({})
        return items, total
