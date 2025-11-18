from pydantic import BaseModel
from typing import Optional, Dict, Any

class Link(BaseModel):
    href: str
    type: Optional[str] = None

class WithLinks(BaseModel):
    _links: Dict[str, Link]

class EventIn(BaseModel):
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = None

class EventOut(WithLinks):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = None
    available_seats: Optional[int] = None

    class Config:
        from_attributes = True


class EventItem(BaseModel):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str]
    total_seats: Optional[int]
    available_seats: Optional[int]
    _links: dict[str, Any]


class EventListResponse(BaseModel):
    items: list[EventItem]
    page: Optional[int] = None
    items_per_page: Optional[int] = None
    total_items: Optional[int] = None
    _links: dict[str, Any]



class PackageIn(BaseModel):
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = None


class PackageOut(WithLinks):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = None
    available_tickets: Optional[int] = None

    class Config:
        from_attributes = True


class PackageItem(BaseModel):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str]
    total_seats: Optional[int]
    available_tickets: Optional[int]
    _links: dict[str, Any]


class PackageListResponse(BaseModel):
    items: list[PackageItem]
    page: int
    items_per_page: int
    total_items: int
    _links: dict[str, Any]

class TicketIn(BaseModel):
    event_id: Optional[int] = None
    package_id: Optional[int] = None

class TicketOut(WithLinks):
    code: str
    event_id: Optional[int]
    package_id: Optional[int]

    class Config:
        from_attributes = True
