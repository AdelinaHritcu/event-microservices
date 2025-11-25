from __future__ import annotations

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr

from app.dtos.events_schemas import EventOut
from app.dtos.packages_schemas import PackageOut


class Link(BaseModel):
    href: str
    type: Optional[str] = None


class SocialLinks(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    public_social: Optional[bool] = False


class TicketInfo(BaseModel):
    code: str
    event_id: Optional[int] = None
    package_id: Optional[int] = None
    event_name: Optional[str] = None
    location: Optional[str] = None


class ClientBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    public_name: Optional[bool] = False
    social: Optional[SocialLinks] = None
    tickets: Optional[List[TicketInfo]] = None


class ClientIn(ClientBase):
    pass


class ClientOut(ClientBase):
    links: Optional[Dict[str, Link]] = Field(
        default=None,
        serialization_alias="_links",
    )

    class Config:
        from_attributes = True


class ClientItem(ClientOut):
    pass


class ClientListResponse(BaseModel):
    items: List[ClientItem]
    page: Optional[int] = None
    items_per_page: Optional[int] = None
    total_items: Optional[int] = None

    links: Optional[Dict[str, Link]] = Field(
        default=None,
        serialization_alias="_links",
    )


class ClientTicketDetailsResponse(BaseModel):
    client_email: str
    ticket_code: str
    is_valid: bool
    event: Optional[EventOut] = None
    package: Optional[PackageOut] = None

    links: Optional[Dict[str, Link]] = Field(
        default=None,
        serialization_alias="_links",
    )
