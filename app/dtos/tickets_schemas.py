from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator


class Link(BaseModel):
    href: str = Field(min_length=1, max_length=2000)
    type: Optional[str] = Field(default=None, max_length=50)


class TicketIn(BaseModel):
    package_id: Optional[int] = Field(default=None, ge=1)
    event_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("package_id", "event_id")
    def validate_ids(cls, value):
        if value is not None and value < 1:
            raise ValueError("ID must be greater than or equal to 1.")
        return value

    @field_validator("event_id")
    def validate_relation(cls, event_id, info):
        package_id = info.data.get("package_id")
        if event_id is None and package_id is None:
            raise ValueError("A ticket must be linked to either a package or an event.")
        return event_id


class TicketItem(BaseModel):
    code: str
    package_id: Optional[int] = Field(default=None, ge=1)
    event_id: Optional[int] = Field(default=None, ge=1)

    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    code: str = Field(min_length=3, max_length=100)
    package_id: Optional[int] = Field(default=None, ge=1)
    event_id: Optional[int] = Field(default=None, ge=1)

    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

    class Config:
        from_attributes = True


class TicketListResponse(BaseModel):
    items: List[TicketItem]
    page: Optional[int] = Field(default=None, ge=1)
    items_per_page: Optional[int] = Field(default=None, ge=1, le=100)
    total_items: Optional[int] = Field(default=None, ge=0)

    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

class AddTicketToClient(BaseModel):
    code: str