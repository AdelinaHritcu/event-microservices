from peewee import MySQLDatabase

from app.database.mariadb_connection import db
from app.database.models import Event, Package, EventPackage, Ticket


def init_db():
    with db:
        db.create_tables([Event, Package, EventPackage, Ticket])
        if isinstance(db, MySQLDatabase):
            # Lab 1, tables 1-2: `locatie` is NULLABLE. Idempotent migration for
            # databases created by an older version where the column was NOT NULL.
            for table in (Event._meta.table_name, Package._meta.table_name):
                db.execute_sql(f"ALTER TABLE `{table}` MODIFY `location` VARCHAR(128) NULL")


if __name__ == "__main__":
    init_db()
