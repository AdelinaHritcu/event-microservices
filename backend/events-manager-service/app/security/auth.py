from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.integrations.idm_client import validate_token

security = HTTPBearer(description="JWS issued by the IDM service (POST /auth/login on Client WebService)")


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

    return Principal(sub=sub, role=role, email=email)


def require_roles(*roles: str):
    roles_set = set(roles)

    def _dep(p: Principal = Depends(require_auth)) -> Principal:
        if p.role not in roles_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return p

    return _dep


def require_owner(owner_id: str, p: Principal) -> None:
    """An owner-event fully manages only the events/packages it created (ID_OWNER)."""
    if p.role == "owner-event" and p.sub == owner_id:
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden: not owner")
