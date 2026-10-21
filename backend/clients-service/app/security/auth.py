from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.integrations.idm_client import validate_token

security = HTTPBearer()


@dataclass(frozen=True)
class Principal:
    sub: str
    role: str


def require_auth(creds: HTTPAuthorizationCredentials = Depends(security)) -> Principal:
    token = (creds.credentials or "").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    valid, sub, role, message = validate_token(token)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=message or "unauthorized")

    return Principal(sub=sub, role=role)


def bearer_token(creds: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Raw bearer token, forwarded on chain calls to Event WebService."""
    return (creds.credentials or "").strip()


def require_roles(*roles: str):
    roles_set = set(roles)

    def _dep(p: Principal = Depends(require_auth)) -> Principal:
        if p.role not in roles_set:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return p

    return _dep

from fastapi import Depends, HTTPException, status

def require_self_or_admin(client_id: str, p: Principal) -> None:
    if p.role == "admin":
        return
    if p.role == "client" and p.sub == client_id:
        return

    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
