# app/controllers/deps.py
from app.database.mariadb_connection import db


def get_db():
    with db.connection_context():
        yield db
