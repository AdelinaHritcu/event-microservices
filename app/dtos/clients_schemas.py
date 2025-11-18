from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class TicketRef(BaseModel):
    ticket_code: str
    mode: str = Field("short", pattern="^(short|long)$")
    event_name: Optional[str] = None
    event_location: Optional[str] = None
    package_name: Optional[str] = None


class ClientBase(BaseModel):
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_name_public: bool = True
    social_links: Optional[Dict[str, Optional[str]]] = None


class ClientIn(ClientBase):
    tickets: Optional[List[TicketRef]] = None


class ClientOut(ClientBase):
    id: str
    tickets: List[TicketRef] = Field(default_factory=list)


class TicketValidationRequest(BaseModel):
    ticket_code: str


class TicketValidationResponse(BaseModel):
    valid: bool
    reason: Optional[str] = None
    event_name: Optional[str] = None
    event_location: Optional[str] = None
    package_name: Optional[str] = None
