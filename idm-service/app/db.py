import os
import sqlite3
from typing import Optional, Tuple

DB_PATH = os.getenv("IDM_SQLITE_PATH", "/data/idm.db")

def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con

def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    con = _conn()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin','owner-event','client'))
    );
    """)

    cur.execute("SELECT COUNT(*) AS c FROM users;")
    if cur.fetchone()["c"] == 0:
        cur.execute("INSERT INTO users(email,password_hash,role) VALUES(?,?,?)",
                    ("admin@test.com", "TO_BE_SET", "admin"))
        cur.execute("INSERT INTO users(email,password_hash,role) VALUES(?,?,?)",
                    ("owner@test.com", "TO_BE_SET", "owner-event"))
        cur.execute("INSERT INTO users(email,password_hash,role) VALUES(?,?,?)",
                    ("client@test.com", "TO_BE_SET", "client"))

    con.commit()
    con.close()

def get_user_by_email(email: str) -> Optional[Tuple[int, str, str]]:
    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT id, password_hash, role FROM users WHERE email = ?;", (email,))
    row = cur.fetchone()
    con.close()
    if not row:
        return None
    return int(row["id"]), str(row["password_hash"]), str(row["role"])

def set_password_hash_if_placeholder(email: str, new_hash: str) -> None:
    con = _conn()
    cur = con.cursor()
    cur.execute("UPDATE users SET password_hash=? WHERE email=? AND password_hash='TO_BE_SET';", (new_hash, email))
    con.commit()
    con.close()
