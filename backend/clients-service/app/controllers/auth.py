import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.integrations.idm_client import login as idm_login

log = logging.getLogger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginIn(BaseModel):
    email: str
    password: str

class LoginOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"

@router.post("/login", response_model=LoginOut)
def login(body: LoginIn):
    try:
        token = idm_login(body.email, body.password)
    except Exception as e:
        log.exception("IDM login failed")
        raise HTTPException(
            status_code=502,
            detail=f"IDM unavailable: {type(e).__name__}: {e}",
        )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid credentials",
        )

    return LoginOut(access_token=token)
