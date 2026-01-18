from peewee import (
    Model, AutoField, IntegerField, CharField, TextField, ForeignKeyField,
    CompositeKey, Check
)
from app.database.mariadb_connection import db


class BaseModel(Model):
    class Meta:
        database = db

class Event(BaseModel):
    DoesNotExist = None
    id = AutoField()
    id_owner = IntegerField(index=True)
    name = CharField(unique=True, max_length=128)
    location = CharField(max_length=128)
    description = TextField(null=True)
    total_seats = IntegerField(
        null=True,
        constraints=[Check('total_seats IS NULL OR total_seats >= 0')]
    )

    class Meta:
        table_name = 'Event'


class Package(BaseModel):
    DoesNotExist = None
    id = AutoField()
    id_owner = IntegerField(index=True)
    name = CharField(unique=True, max_length=128)
    location = CharField(max_length=128)
    description = TextField(null=True)
    total_seats = IntegerField(
        null=True,
        constraints=[Check('total_seats IS NULL OR total_seats >= 0')]
    )

    class Meta:
        table_name = 'Package'


class EventPackage(BaseModel):
    package = ForeignKeyField(
        Package, backref='event_packages', column_name='package_id',
        on_delete='CASCADE'
    )
    event = ForeignKeyField(
        Event, backref='event_packages', column_name='event_id',
        on_delete='CASCADE'
    )

    class Meta:
        table_name = 'EventPackage'
        primary_key = CompositeKey('package', 'event')


class Ticket(BaseModel):
    code = CharField(primary_key=True, max_length=64, column_name='ticket_code')
    package = ForeignKeyField(
        Package, backref='tickets', column_name='package_id',
        null=True, on_delete='CASCADE'
    )
    event = ForeignKeyField(
        Event, backref='tickets', column_name='event_id',
        null=True, on_delete='CASCADE'
    )

    class Meta:
        table_name = 'Ticket'
        constraints = [
            Check('(package_id IS NULL) <> (event_id IS NULL)')
        ]
