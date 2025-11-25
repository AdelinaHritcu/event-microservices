import os
from dotenv import load_dotenv

load_dotenv()

def get_env(name: str, default=None, required=False):
    v = os.getenv(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return v

# MariaDB
DB_NAME = get_env("DB_NAME", required=True)
DB_USER = get_env("DB_USER", required=True)
DB_PASS = get_env("DB_PASS", required=True)
DB_HOST = get_env("DB_HOST", "mariadb")
DB_PORT = int(get_env("DB_PORT", "3306"))

# MongoDB
MONGO_HOST = get_env("MONGO_HOST", "mongo")
MONGO_PORT = int(get_env("MONGO_PORT", "27017"))
MONGO_DB_NAME = get_env("MONGO_DB_NAME", required=True)
MONGO_APP_USER = get_env("MONGO_APP_USER", required=True)
MONGO_APP_PASS = get_env("MONGO_APP_PASS", required=True)
MONGO_CLIENTS_COLLECTION = get_env("MONGO_CLIENTS_COLLECTION", "clients")

MONGO_URI = (
    f"mongodb://{MONGO_APP_USER}:{MONGO_APP_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
    f"{MONGO_DB_NAME}?authSource={MONGO_DB_NAME}"
)
