from __future__ import annotations

from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, EmailStr, model_validator


class Link(BaseModel):
    href: str
    type: Optional[str] = None


class SocialLinks(BaseModel):
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    tiktok: Optional[str] = None
    public_social: Optional[bool] = False


class TicketInfo(BaseModel):
    """Ticket stored in the client document – long format (Lab 3 / Table 3)."""
    code: str
    event_id: Optional[int] = None
    package_id: Optional[int] = None
    event_name: Optional[str] = None
    location: Optional[str] = None
    events: Optional[List[dict]] = None  # events included in a package


class ClientProfile(BaseModel):
    """Personal data – every field optional (stored only when present)."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    public_name: Optional[bool] = None
    social: Optional[SocialLinks] = None


class ClientIn(ClientProfile):
    email: EmailStr


class ClientUpdate(ClientProfile):
    """PUT body: only personal data; email and tickets cannot be changed here."""
    pass


class ClientOut(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id", serialization_alias="id")
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    public_name: Optional[bool] = False
    social: Optional[SocialLinks] = None
    tickets: List[TicketInfo] = Field(default_factory=list)
    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

    class Config:
        populate_by_name = True
        from_attributes = True


class ClientListResponse(BaseModel):
    items: List[ClientOut]
    page: int
    items_per_page: int
    total_items: int
    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")


class PublicClientOut(BaseModel):
    """What an owner-event may see about a buyer: only fields flagged as public."""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    social: Optional[SocialLinks] = None
    tickets: List[TicketInfo] = Field(default_factory=list)


class BuyersResponse(BaseModel):
    items: List[PublicClientOut]
    total_items: int
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

    @model_validator(mode="after")
    def validate_relation(self):
        if (self.event_id is None) == (self.package_id is None):
            raise ValueError("Provide exactly one between event_id and package_id")
        return self


# ------------------------------------------------------------ users (IDM)

class UserIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: Literal["owner-event", "client"]


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")
