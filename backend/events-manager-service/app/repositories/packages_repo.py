from typing import List
from app.database.models import Event, Package, EventPackage, Ticket


class PackagesRepository:

    @staticmethod
    def get_by_id(package_id: int) -> Package:
        if package_id <= 0:
            raise ValueError("package_id must be positive")
        return Package.get(Package.id == package_id)

    @staticmethod
    def create(data: dict) -> Package:
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        allowed_fields = {"id_owner", "name", "location", "description", "total_seats"}
        clean_data = {k: v for k, v in data.items() if k in allowed_fields}

        if "name" not in clean_data or "id_owner" not in clean_data:
            raise ValueError("id_owner and name are required")

        return Package.create(**clean_data)

    @staticmethod
    def update(package: Package, data: dict) -> Package:
        if package is None:
            raise ValueError("package cannot be None")
        if not isinstance(data, dict):
            raise TypeError("data must be a dict")

        allowed_fields = {"id_owner", "name", "location", "description", "total_seats"}
        clean_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not clean_data:
            return package

        for key, value in clean_data.items():
            setattr(package, key, value)

        package.save()
        return package

    @staticmethod
    def delete(package: Package) -> None:
        if package is None:
            raise ValueError("package cannot be None")
        package.delete_instance()

    @staticmethod
    def count_sold_tickets(package: Package) -> int:
        if package is None:
            raise ValueError("package cannot be None")
        return Ticket.select().where(Ticket.package == package).count()

    @staticmethod
    def list_all() -> List[Package]:
        return list(Package.select().order_by(Package.id))

    @staticmethod
    def list_by_description_contains(text: str) -> List[Package]:
        if not text:
            return PackagesRepository.list_all()
        query = (
            Package.select()
            .where(Package.description.contains(text))
            .order_by(Package.id)
        )
        return list(query)

    @staticmethod
    def list_events_for_package(package_id: int) -> List[Event]:
        if package_id <= 0:
            raise ValueError("package_id must be positive")
        query = (
            Event.select()
            .join(EventPackage)
            .where(EventPackage.package == package_id)
            .order_by(Event.id)
        )
        return list(query)

    @staticmethod
    def list_packages_for_event(event_id: int) -> List[Package]:
        if event_id <= 0:
            raise ValueError("event_id must be positive")
        query = (
            Package.select()
            .join(EventPackage)
            .where(EventPackage.event == event_id)
            .order_by(Package.id)
        )
        return list(query)

    @staticmethod
    def get_link(package_id: int, event_id: int):
        return EventPackage.get_or_none(
            (EventPackage.package == package_id) & (EventPackage.event == event_id)
        )

    @staticmethod
    def add_link(package_id: int, event_id: int) -> EventPackage:
        return EventPackage.create(package=package_id, event=event_id)

    @staticmethod
    def remove_link(package_id: int, event_id: int) -> bool:
        return (
            EventPackage.delete()
            .where((EventPackage.package == package_id) & (EventPackage.event == event_id))
            .execute()
            > 0
        )
