import os
from functools import lru_cache

import grpc

from app import idm_pb2, idm_pb2_grpc


def _target() -> str:
    host = os.getenv("IDM_GRPC_HOST", "pos-idm-service")
    port = os.getenv("IDM_GRPC_PORT", "50051")
    return f"{host}:{port}"


def _use_tls() -> bool:
    v = os.getenv("IDM_GRPC_TLS", "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _creds() -> grpc.ChannelCredentials:
    cert_path = os.getenv("IDM_TLS_ROOT_CERT", "/certs/idm.crt")
    try:
        with open(cert_path, "rb") as f:
            root_cert = f.read()
    except FileNotFoundError as e:
        raise RuntimeError(f"Missing IDM root cert at {cert_path}") from e
    return grpc.ssl_channel_credentials(root_certificates=root_cert)


@lru_cache(maxsize=1)
def _stub() -> idm_pb2_grpc.IdmServiceStub:
    # one channel per process; gRPC channels are thread-safe and reconnect on their own
    if _use_tls():
        ch = grpc.secure_channel(_target(), _creds())
    else:
        ch = grpc.insecure_channel(_target())
    return idm_pb2_grpc.IdmServiceStub(ch)


def _md(token: str):
    return [("authorization", f"Bearer {token}")]


def login(username: str, password: str) -> str:
    r = _stub().Login(idm_pb2.LoginRequest(username=username, password=password), timeout=5)
    return r.token


def validate_token(token: str):
    r = _stub().ValidateToken(idm_pb2.TokenRequest(token=token), timeout=5)
    return r.valid, r.sub, r.role, r.email, r.message


def logout(token: str):
    r = _stub().Logout(idm_pb2.TokenRequest(token=token), metadata=_md(token), timeout=5)
    return r.success, r.message


def create_user(token: str, email: str, password: str, role: str):
    r = _stub().CreateUser(
        idm_pb2.CreateUserRequest(email=email, password=password, role=role),
        metadata=_md(token),
        timeout=5,
    )
    return r.success, r.message, r.sub, r.role


def list_users(token: str) -> list[dict]:
    r = _stub().ListUsers(idm_pb2.ListUsersRequest(), metadata=_md(token), timeout=5)
    return [{"id": u.id, "email": u.email, "role": u.role} for u in r.users]


def delete_user(token: str, user_id: str):
    r = _stub().DeleteUser(idm_pb2.DeleteUserRequest(id=user_id), metadata=_md(token), timeout=5)
    return r.success, r.message
