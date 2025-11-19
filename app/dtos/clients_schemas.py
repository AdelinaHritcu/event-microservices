from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field, EmailStr


class TicketRef(BaseModel):
    ticket_code: str
    mode: Literal["short", "long"] = "short"
    event_name: Optional[str] = None
    event_location: Optional[str] = None
    package_name: Optional[str] = None


class ClientBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_name_public: bool = True
    social_links: Optional[Dict[str, Optional[str]]] = None


class ClientIn(ClientBase):
    tickets: List[TicketRef] = Field(default_factory=list)


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
