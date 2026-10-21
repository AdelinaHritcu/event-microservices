from __future__ import annotations

from typing import Optional, List, Dict
from pydantic import BaseModel, Field, EmailStr, field_validator


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
    events: Optional[List[dict]] = None  # long format for package tickets


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
    id: Optional[str] = Field(default=None, alias="_id", serialization_alias="id")
    tickets: List[TicketInfo] = Field(default_factory=list)
    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

    class Config:
        populate_by_name = True
        from_attributes = True


class ClientItem(ClientOut):
    pass


class ClientListResponse(BaseModel):
    items: List[ClientItem]
    page: Optional[int] = None
    items_per_page: Optional[int] = None
    total_items: Optional[int] = None
    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")


class ClientTicketDetailsResponse(BaseModel):
    client_id: str
    client_email: Optional[EmailStr] = None
    ticket_code: str
    is_valid: bool
    event: Optional[dict] = None
    package: Optional[dict] = None
    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

class AddTicketToClient(BaseModel):
    event_id: Optional[int] = Field(default=None, ge=1)
    package_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("event_id")
    def validate_relation(cls, event_id, info):
        package_id = info.data.get("package_id")
        if (event_id is None and package_id is None) or (
            event_id is not None and package_id is not None
        ):
            raise ValueError("Provide exactly one between event_id and package_id")
        return event_id