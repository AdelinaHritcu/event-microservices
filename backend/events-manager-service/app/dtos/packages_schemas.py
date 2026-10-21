from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator


class Link(BaseModel):
    href: str = Field(min_length=1, max_length=2000)
    type: Optional[str] = Field(default=None, max_length=50)


class PackageIn(BaseModel):
    id_owner: Optional[int] = Field(
        default=None, ge=1, description="Ignored: the owner is always taken from the JWS (sub)."
    )
    name: str = Field(min_length=3, max_length=100)
    location: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    total_seats: Optional[int] = Field(default=None)

    @field_validator("total_seats")
    def validate_total_seats(cls, value: Optional[int]):
        if value is not None and value < 0:
            raise ValueError("Total seats cannot be lower than 0.")
        return value


class PackageItem(BaseModel):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = Field(default=None, ge=0)
    available_tickets: Optional[int] = Field(default=None, ge=0)

    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

    @field_validator("available_tickets")
    def validate_available_tickets(cls, value: Optional[int], info):
        if value is None:
            return value
        total_seats = info.data.get("total_seats")
        if total_seats is not None and value > total_seats:
            raise ValueError("Available tickets cannot be greater than total seats.")
        return value

    class Config:
        from_attributes = True


class PackageOut(BaseModel):
    id: int
    id_owner: int
    name: str
    location: str
    description: Optional[str] = None
    total_seats: Optional[int] = Field(default=None, ge=0)
    available_tickets: Optional[int] = Field(default=None, ge=0)

    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")

    @field_validator("available_tickets")
    def validate_available_tickets(cls, value: Optional[int], info):
        if value is None:
            return value
        total_seats = info.data.get("total_seats")
        if total_seats is not None and value > total_seats:
            raise ValueError("Available tickets cannot be greater than total seats.")
        return value

    class Config:
        from_attributes = True


class PackageListResponse(BaseModel):
    items: List[PackageItem]
    page: Optional[int] = Field(default=None, ge=1)
    items_per_page: Optional[int] = Field(default=None, ge=1, le=100)
    total_items: Optional[int] = Field(default=None, ge=0)

    links: Optional[Dict[str, Link]] = Field(default=None, serialization_alias="_links")
