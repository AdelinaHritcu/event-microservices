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

def get_env(name: str, default=None, required: bool = False):
    v = os.getenv(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return v

def get_secret(env_name: str, file_env_name: str, required: bool = False, default=None):
    v = _read_file(os.getenv(file_env_name)) or os.getenv(env_name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Missing required secret/env: {env_name} or {file_env_name}")
    return v

DB_NAME = get_env("DB_NAME", required=True)
DB_USER = get_env("DB_USER", required=True)
DB_PASS = get_secret("DB_PASS", "DB_PASS_FILE", required=True)

DB_HOST = get_env("DB_HOST", "mariadb")
DB_PORT = int(get_env("DB_PORT", "3306"))
