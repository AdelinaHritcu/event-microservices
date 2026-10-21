from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.integrations.idm_client import validate_token

security = HTTPBearer(description="JWS issued by the IDM service (POST /auth/login)")


@dataclass(frozen=True)
class Principal:
    sub: str
    role: str
    email: str = ""


def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> Principal:
    token = (creds.credentials or "").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    try:
        valid, sub, role, email, message = validate_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="IDM service unavailable")

    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message or "unauthorized")

    return Principal(sub=sub, role=role, email=(email or "").lower())


def bearer_token(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Raw bearer token, forwarded on chain calls to Event WebService / IDM."""
    return (creds.credentials or "").strip()


def require_roles(*roles: str):
    roles_set = set(roles)

    def _dep(p: Principal = Depends(require_auth)) -> Principal:
        if p.role not in roles_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return p

    return _dep


def require_self_or_admin(client_doc: dict, p: Principal) -> None:
    """
    Lab 4 / 3.2.2: an IDM user is mapped to its client document through `email`.
    """
    if p.role == "admin":
        return
    if p.role == "client" and p.email and str(client_doc.get("email", "")).lower() == p.email:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
