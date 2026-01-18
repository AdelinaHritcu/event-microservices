from peewee import MySQLDatabase
from app.database.config import (
    DB_NAME,
    DB_USER,
    DB_PASS,
    DB_HOST,
    DB_PORT,
)

db = MySQLDatabase(
    DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT,
    charset="utf8mb4",
)
