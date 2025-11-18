from pymongo import MongoClient
from app.database.config import MONGO_URI, MONGO_DB_NAME, MONGO_CLIENTS_COLLECTION

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
clients_collection = db[MONGO_CLIENTS_COLLECTION]
