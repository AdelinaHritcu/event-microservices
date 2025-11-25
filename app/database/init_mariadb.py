from app.database.mariadb_connection import db
from app.database.models import Event, Package, EventPackage, Ticket


def init_db():
    with db:
        db.create_tables([Event, Package, EventPackage, Ticket])


if __name__ == "__main__":
    init_db()
