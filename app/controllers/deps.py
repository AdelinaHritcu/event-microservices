# app/controllers/deps.py
from fastapi import Depends
from contextlib import contextmanager
from app.database.mariadb_connection import db

@contextmanager
def db_ctx():
    with db.connection_context():
        yield db

def get_db(dbx=Depends(db_ctx)):
    return db
