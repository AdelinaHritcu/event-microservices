from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator


class Link(BaseModel):
    href: str = Field(min_length=1, max_length=2000)
    type: Optional[str] = Field(default=None, max_length=50)


class EventIn(BaseModel):
    id_owner: int = Field(
        ge=1,
        description="ID of the user who owns the event."
    )
    name: str = Field(
        min_length=3,
        max_length=100,
        description="Name of the event."
    )
    location: str = Field(
        min_length=3,
        max_length=100,
        description="Location of the event."
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional description of the event."
    )
    total_seats: Optional[int] = Field(
        default=None,
        description="Total number of seats available."
    )

    @field_validator("total_seats")
    def validate_total_seats(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 0:
            raise ValueError("Total seats cannot be lower than 0.")
        return value


class EventOut(BaseModel):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = Field(default=None, ge=0)
    available_seats: Optional[int] = Field(default=None, ge=0)

    links: Optional[Dict[str, Link]] = Field(
        default=None,
        serialization_alias="_links"
    )

    class Config:
        from_attributes = True


class EventItem(BaseModel):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = Field(default=None, ge=0)
    available_seats: Optional[int] = Field(default=None, ge=0)

    links: Optional[Dict[str, Link]] = Field(
        default=None,
        serialization_alias="_links"
    )

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    items: List[EventItem]
    page: Optional[int] = Field(default=None, ge=1)
    items_per_page: Optional[int] = Field(default=None, ge=1, le=100)
    total: Optional[int] = Field(default=None, ge=0)

    links: Optional[Dict[str, Link]] = Field(
        default=None,
        serialization_alias="_links"
    )
