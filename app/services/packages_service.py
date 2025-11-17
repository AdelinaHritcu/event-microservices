from typing import Optional

from app.database.models import Event, Package
from app.repositories import packages_repo


def compute_available_tickets(package: Package) -> Optional[int]:
    if package.total_seats is None:
        return None
    sold = packages_repo.count_sold_tickets(package)
    return max(package.total_seats - sold, 0)


def list_packages(
    page: int,
    per_page: int,
    available_tickets: Optional[int] = None,
    type_query: Optional[str] = None,
) -> tuple[list[tuple[Package, Optional[int]]], int]:
    if type_query:
        packages = packages_repo.list_by_description_contains(type_query)
    else:
        packages = packages_repo.list_all()

    items: list[tuple[Package, Optional[int]]] = []
    for package in packages:
        available = compute_available_tickets(package)
        if available_tickets is not None:
            if available is None or available < available_tickets:
                continue
        items.append((package, available))

    total = len(items)
    start = (page - 1) * per_page
    end = start + per_page

    return items[start:end], total


def get_package(package_id: int) -> Package:
    return packages_repo.get_by_id(package_id)


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
    return packages_repo.create(data)


def update_package(
    package: Package,
    name: Optional[str],
    location: Optional[str],
    description: Optional[str],
    total_seats: Optional[int],
) -> Package:
    data: dict = {}
    if name is not None:
        data["name"] = name
    if location is not None:
        data["location"] = location
    if description is not None:
        data["description"] = description
    if total_seats is not None:
        data["total_seats"] = total_seats
    return packages_repo.update(package, data)


def delete_package(package: Package) -> None:
    packages_repo.delete(package)


def list_events_for_package(package_id: int) -> list[Event]:
    return packages_repo.list_events_for_package(package_id)

def list_packages_for_event(event_id: int) -> list[Package]:
    return packages_repo.list_packages_for_event(event_id)
