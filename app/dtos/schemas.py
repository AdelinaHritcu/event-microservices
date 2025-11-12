# app/dtos/schemas.py
from pydantic import BaseModel
from typing import Optional, Dict

class Link(BaseModel):
    href: str
    type: Optional[str] = None

class WithLinks(BaseModel):
    _links: Dict[str, Link]

# EVENTS
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
    class Config: from_attributes = True

# PACKAGES
class PackageIn(BaseModel):
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None

class PackageOut(WithLinks):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    class Config: from_attributes = True

# TICKETS
class TicketIn(BaseModel):
    code: str
    event_id: Optional[int] = None
    package_id: Optional[int] = None

class TicketOut(WithLinks):
    code: str
    event_id: Optional[int]
    package_id: Optional[int]
    class Config: from_attributes = True
