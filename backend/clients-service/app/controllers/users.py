"""
User management for the application administrator (Lab 1 / 1.4, Lab 4 / 3.2.1).
Thin REST facade over the IDM gRPC service; the admin cannot reach any other data.
"""
from typing import List

import grpc
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from app.dtos.clients_schemas import UserIn, UserOut, Link
from app.integrations import idm_client
from app.repositories.clients_repo import ClientsRepository
from app.security.auth import require_roles, Principal, bearer_token
from app.services.clients_service import ClientsService

BASE = "/api/users"

router = APIRouter(prefix=BASE, tags=["users"])


def _links(user_id: str):
    return {
        "self": Link(href=f"{BASE}/{user_id}", type="DELETE"),
        "parent": Link(href=BASE, type="GET"),
    }


def _idm_error(e: grpc.RpcError):
    if e.code() == grpc.StatusCode.INVALID_ARGUMENT:
        raise HTTPException(status_code=422, detail=e.details())
    if e.code() == grpc.StatusCode.PERMISSION_DENIED:
        raise HTTPException(status_code=403, detail="forbidden")
    if e.code() == grpc.StatusCode.UNAUTHENTICATED:
        raise HTTPException(status_code=401, detail=e.details())
    raise HTTPException(status_code=503, detail="IDM service unavailable")


@router.get("", response_model=List[UserOut])
def list_users(
    p: Principal = Depends(require_roles("admin")),
    token: str = Depends(bearer_token),
):
    try:
        users = idm_client.list_users(token)
    except grpc.RpcError as e:
        _idm_error(e)
    return [UserOut(**u, links=_links(u["id"])) for u in users]


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    body: UserIn,
    p: Principal = Depends(require_roles("admin")),
    token: str = Depends(bearer_token),
):
    """Creates an owner-event or client account. For clients, the MongoDB document is created too (mapped by email)."""
    email = str(body.email).lower()
    try:
        ok, message, sub, role = idm_client.create_user(token, email, body.password, body.role)
    except grpc.RpcError as e:
        _idm_error(e)
    if not ok:
        raise HTTPException(status_code=409, detail=message or "user already exists")

    if role == "client":
        ClientsService.ensure_client_document(email)

    return UserOut(id=sub, email=email, role=role, links=_links(sub))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    p: Principal = Depends(require_roles("admin")),
    token: str = Depends(bearer_token),
):
    if user_id == p.sub:
        raise HTTPException(status_code=409, detail="admin cannot delete itself")
    try:
        users = {u["id"]: u for u in idm_client.list_users(token)}
        if user_id not in users:
            raise HTTPException(status_code=404, detail="User not found")
        ok, message = idm_client.delete_user(token, user_id)
    except grpc.RpcError as e:
        _idm_error(e)
    if not ok:
        raise HTTPException(status_code=404, detail=message or "User not found")
    if users[user_id]["role"] == "client":
        ClientsRepository.delete_client_by_email(users[user_id]["email"])
    return Response(status_code=status.HTTP_204_NO_CONTENT)
