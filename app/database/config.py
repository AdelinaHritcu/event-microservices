import os
from dotenv import load_dotenv

load_dotenv()

def get_env(name: str, default=None, required=False):
    v = os.getenv(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return v

DB_NAME = get_env("DB_NAME", required=True)
DB_USER = get_env("DB_USER", required=True)
DB_PASS = get_env("DB_PASS", required=True)
DB_HOST = get_env("DB_HOST", "127.0.0.1")
DB_PORT = int(get_env("DB_PORT", "3306"))

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "pos_event_manager")
MONGO_CLIENTS_COLLECTION = os.getenv("MONGO_CLIENTS_COLLECTION", "clients")
