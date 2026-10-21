"""
IDM user store – MariaDB (separate container, Lab 5).

Table `users` follows Lab 1 / Table 6:
  id        INT          PK, auto increment
  email     VARCHAR      UK  (username)
  password  VARCHAR      NOT NULL (bcrypt hash)
  role      ENUM         NOT NULL ('admin', 'owner-event', 'client')
"""
import os
import time
from typing import Optional, Tuple, List

import pymysql
from pymysql.cursors import DictCursor

ROLES = ("admin", "owner-event", "client")


def _read_secret(env_name: str, file_env_name: str) -> Optional[str]:
    path = os.getenv(file_env_name)
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            pass
    return os.getenv(env_name)


def _conn() -> pymysql.connections.Connection:
    return pymysql.connect(
        host=os.getenv("IDM_DB_HOST", "idm-db"),
        port=int(os.getenv("IDM_DB_PORT", "3306")),
        user=os.getenv("IDM_DB_USER", "idm"),
        password=_read_secret("IDM_DB_PASS", "IDM_DB_PASS_FILE") or "",
        database=os.getenv("IDM_DB_NAME", "idm"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=True,
    )


def init_db(retries: int = 30, delay: float = 2.0) -> None:
    last_err: Optional[Exception] = None
    for _ in range(retries):
        try:
            con = _conn()
            break
        except pymysql.err.OperationalError as e:
            last_err = e
            time.sleep(delay)
    else:
        raise RuntimeError(f"IDM database unreachable: {last_err}")

    with con, con.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('admin','owner-event','client') NOT NULL
            )
            """
        )
        cur.execute("SELECT COUNT(*) AS c FROM users")
        if cur.fetchone()["c"] == 0:
            # demo accounts; real passwords are hashed on first login (see server.py)
            cur.executemany(
                "INSERT INTO users(email, password_hash, role) VALUES (%s, %s, %s)",
                [
                    ("admin@test.com", "TO_BE_SET", "admin"),
                    ("owner@test.com", "TO_BE_SET", "owner-event"),
                    ("client@test.com", "TO_BE_SET", "client"),
                ],
            )


def get_user_by_email(email: str) -> Optional[Tuple[int, str, str]]:
    with _conn() as con, con.cursor() as cur:
        cur.execute("SELECT id, password_hash, role FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
    if not row:
        return None
    return int(row["id"]), str(row["password_hash"]), str(row["role"])


def set_password_hash_if_placeholder(email: str, new_hash: str) -> None:
    with _conn() as con, con.cursor() as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s AND password_hash = 'TO_BE_SET'",
            (new_hash, email),
        )


def create_user(email: str, password_hash: str, role: str) -> Optional[int]:
    try:
        with _conn() as con, con.cursor() as cur:
            cur.execute(
                "INSERT INTO users(email, password_hash, role) VALUES (%s, %s, %s)",
                (email, password_hash, role),
            )
            return int(cur.lastrowid)
    except pymysql.err.IntegrityError:
        return None


def list_users() -> List[dict]:
    with _conn() as con, con.cursor() as cur:
        cur.execute("SELECT id, email, role FROM users ORDER BY id")
        return list(cur.fetchall())


def delete_user(user_id: int) -> bool:
    with _conn() as con, con.cursor() as cur:
        return cur.execute("DELETE FROM users WHERE id = %s", (user_id,)) > 0
