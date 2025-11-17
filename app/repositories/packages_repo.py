from typing import Optional, List, Tuple
from peewee import DoesNotExist

from app.database.models import Event, Package, EventPackage, Ticket


def get_by_id(package_id: int) -> Package:
    return Package.get(Package.id == package_id)


def create(data: dict) -> Package:
    return Package.create(**data)


def update(package: Package, data: dict) -> Package:
    for key, value in data.items():
        setattr(package, key, value)
    package.save()
    return package


def delete(package: Package) -> None:
    package.delete_instance()


def count_sold_tickets(package: Package) -> int:
    return Ticket.select().where(Ticket.package == package).count()


def list_all() -> list[Package]:
    return list(Package.select().order_by(Package.id))


def list_by_description_contains(text: str) -> list[Package]:
    query = Package.select().where(Package.description.contains(text)).order_by(Package.id)
    return list(query)


def list_events_for_package(package_id: int) -> list[Event]:
    query = (
        Event.select()
        .join(EventPackage)
        .where(EventPackage.package == package_id)
        .order_by(Event.id)
    )
    return list(query)

def list_packages_for_event(event_id: int) -> list[Package]:
    query = (
        Package.select()
        .join(EventPackage)
        .where(EventPackage.event == event_id)
        .order_by(Package.id)
    )
    return list(query)
