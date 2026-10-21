import logging

import grpc
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel

from app.integrations import idm_client
from app.security.auth import Principal, require_auth, bearer_token

log = logging.getLogger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "Bearer"


class MeOut(BaseModel):
    sub: str
    role: str
    email: str


@router.post("/login", response_model=LoginOut)
def login(body: LoginIn):
    """Public: exchanges credentials for a JWS issued by the IDM gRPC service."""
    try:
        token = idm_client.login(body.email, body.password)
    except grpc.RpcError as e:
        if e.code() in (grpc.StatusCode.UNAUTHENTICATED, grpc.StatusCode.INVALID_ARGUMENT):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
        log.exception("IDM login failed")
        raise HTTPException(status_code=503, detail="IDM service unavailable")
    except Exception:
        log.exception("IDM login failed")
        raise HTTPException(status_code=503, detail="IDM service unavailable")

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    return LoginOut(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    p: Principal = Depends(require_auth),
    token: str = Depends(bearer_token),
):
    """Invalidates the presented token (IDM blacklist)."""
    try:
        idm_client.logout(token)
    except Exception:
        raise HTTPException(status_code=503, detail="IDM service unavailable")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=MeOut)
def me(p: Principal = Depends(require_auth)):
    return MeOut(sub=p.sub, role=p.role, email=p.email)
