from typing import Optional, List
from peewee import DoesNotExist

from app.database.models import Event, Package, EventPackage
from app.repositories.packages_repo import PackagesRepository


def compute_available_tickets(package: Package) -> Optional[int]:
    if package.total_seats is None:
        return None
    sold = PackagesRepository.count_sold_tickets(package)
    return max(package.total_seats - sold, 0)


def list_packages(
    page: int,
    per_page: int,
    available_tickets: Optional[int] = None,
    type_query: Optional[str] = None,
    event_name: Optional[str] = None,
):
    q = Package.select()

    if type_query:
        q = q.where(Package.description.contains(type_query))

    if event_name:
        q = (
            q.join(EventPackage)
             .join(Event)
             .where(Event.name.contains(event_name))
        )

    q = q.distinct()

    filtered = []
    for p in q:
        available = compute_available_tickets(p)
        if (
            available_tickets is not None
            and available is not None
            and available < available_tickets
        ):
            continue
        filtered.append((p, available))

    total = len(filtered)

    start = (page - 1) * per_page
    end = start + per_page
    page_items = filtered[start:end]

    return page_items, total


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
) -> Package:
    data = {}
    if name is not None:
        data["name"] = name
    if location is not None:
        data["location"] = location
    if description is not None:
        data["description"] = description
    if total_seats is not None:
        data["total_seats"] = total_seats
    return PackagesRepository.update(package, data)


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
