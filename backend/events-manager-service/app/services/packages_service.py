from typing import Optional, List, Tuple
from peewee import DoesNotExist

from app.database.mariadb_connection import db
from app.database.models import Event, Package, EventPackage
from app.repositories.packages_repo import PackagesRepository


def compute_available_tickets(package: Package) -> Optional[int]:
    if package.total_seats is None:
        return None
    sold = PackagesRepository.count_sold_tickets(package)
    return max(package.total_seats - sold, 0)


def seats_violation(total_seats: Optional[int], events: List[Event]) -> Optional[str]:
    """Package seats must not exceed min(seats) of its events (Lab 1, 1.1.3)."""
    if total_seats is None:
        return None
    for e in events:
        if e.total_seats is None:
            return f"Event '{e.name}' has no seats configured"
        if total_seats > e.total_seats:
            return (
                f"Package seats ({total_seats}) exceed seats of event "
                f"'{e.name}' ({e.total_seats})"
            )
    return None


def list_packages(
    page: int,
    per_page: int,
    available_tickets: Optional[int] = None,
    type_query: Optional[str] = None,
    event_name: Optional[str] = None,
    name: Optional[str] = None,
    location: Optional[str] = None,
    id_owner: Optional[int] = None,
):
    q = Package.select()

    if id_owner is not None:
        q = q.where(Package.id_owner == id_owner)

    if name:
        q = q.where(Package.name.contains(name))
    if location:
        q = q.where(Package.location.contains(location))
    if type_query:
        q = q.where(Package.description.contains(type_query))

    if event_name:
        q = (
            q.join(EventPackage)
             .join(Event)
             .where(Event.name.contains(event_name))
        )

    q = q.distinct().order_by(Package.id)

    filtered = []
    for p in q:
        available = compute_available_tickets(p)
        if available_tickets is not None and (available is None or available < available_tickets):
            continue
        filtered.append((p, available))

    total = len(filtered)

    start = (page - 1) * per_page
    end = start + per_page
    return filtered[start:end], total


def get_package(package_id: int) -> Optional[Package]:
    try:
        return PackagesRepository.get_by_id(package_id)
    except DoesNotExist:
        return None


def create_package(
    id_owner: int,
    name: str,
    location: str,
    description: Optional[str],
    total_seats: Optional[int],
) -> Package:
    data = {
        "id_owner": id_owner,
        "name": name,
        "location": location,
        "description": description,
        "total_seats": total_seats,
    }
    return PackagesRepository.create(data)


def update_package(
    package: Package,
    name: Optional[str],
    location: Optional[str],
    description: Optional[str],
    total_seats: Optional[int],
    id_owner: Optional[int] = None,
) -> Tuple[int, Package | str]:
    data = {}
    if name is not None:
        data["name"] = name
    if location is not None:
        data["location"] = location
    if description is not None:
        data["description"] = description
    if id_owner is not None:
        data["id_owner"] = id_owner
    if total_seats is not None and total_seats != package.total_seats:
        if PackagesRepository.count_sold_tickets(package) > 0:
            return 409, "Edit locked: tickets already sold for this package"
        err = seats_violation(total_seats, list_events_for_package(package.id))
        if err:
            return 409, err
        data["total_seats"] = total_seats
    return 200, PackagesRepository.update(package, data)


def delete_package(package: Package) -> int:
    if package is None:
        raise ValueError("package cannot be None")

    sold = PackagesRepository.count_sold_tickets(package)
    if sold > 0:
        return 409

    PackagesRepository.delete(package)
    return 204


def list_events_for_package(package_id: int) -> List[Event]:
    return PackagesRepository.list_events_for_package(package_id)


def list_packages_for_event(event_id: int) -> List[Package]:
    return PackagesRepository.list_packages_for_event(event_id)


def add_event_to_package(package: Package, event_id: int) -> Tuple[int, Optional[str]]:
    """Returns (201 created | 204 already linked | 404 | 409, detail)."""
    with db.atomic():
        event = Event.get_or_none(Event.id == event_id)
        if event is None:
            return 404, "Event not found"
        if PackagesRepository.get_link(package.id, event_id):
            return 204, None
        if PackagesRepository.count_sold_tickets(package) > 0:
            return 409, "Package composition locked: tickets already sold"
        err = seats_violation(package.total_seats, [event])
        if err:
            return 409, err
        PackagesRepository.add_link(package.id, event_id)
    return 201, None


def remove_event_from_package(package: Package, event_id: int) -> Tuple[int, Optional[str]]:
    if not PackagesRepository.get_link(package.id, event_id):
        return 404, "Event is not part of this package"
    if PackagesRepository.count_sold_tickets(package) > 0:
        return 409, "Package composition locked: tickets already sold"
    PackagesRepository.remove_link(package.id, event_id)
    return 204, None
