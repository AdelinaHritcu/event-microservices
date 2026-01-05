import os
from dotenv import load_dotenv

load_dotenv()

def _read_file(path: str | None) -> str | None:
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def get_env(name: str, default=None, required=False):
    v = os.getenv(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def get_secret(env_name: str, file_env_name: str, required: bool = False, default=None):
    v = _read_file(os.getenv(file_env_name)) or os.getenv(env_name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required secret/env: {env_name} or {file_env_name}")
    return v

MONGO_HOST = get_env("MONGO_HOST", "mongo")
MONGO_PORT = int(get_env("MONGO_PORT", "27017"))
MONGO_DB_NAME = get_env("MONGO_DB_NAME", required=True)

MONGO_APP_USER = get_env("MONGO_APP_USER", required=True)
MONGO_APP_PASS = get_secret("MONGO_APP_PASS", "MONGO_APP_PASS_FILE", required=True)

MONGO_CLIENTS_COLLECTION = get_env("MONGO_CLIENTS_COLLECTION", "clients")

MONGO_URI = (
    f"mongodb://{MONGO_APP_USER}:{MONGO_APP_PASS}@{MONGO_HOST}:{MONGO_PORT}/"
    f"{MONGO_DB_NAME}?authSource={MONGO_DB_NAME}"
)
