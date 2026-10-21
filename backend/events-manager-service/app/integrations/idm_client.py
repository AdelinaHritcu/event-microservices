import os
from functools import lru_cache

import grpc

from app import idm_pb2, idm_pb2_grpc


def _target() -> str:
    host = os.getenv("IDM_GRPC_HOST", "pos-idm-service")
    port = os.getenv("IDM_GRPC_PORT", "50051")
    return f"{host}:{port}"


@lru_cache(maxsize=1)
def _stub() -> idm_pb2_grpc.IdmServiceStub:
    # one TLS channel per process (thread-safe, reconnects by itself)
    root_path = os.getenv("IDM_TLS_ROOT_CERT", "/certs/idm.crt")
    with open(root_path, "rb") as f:
        root = f.read()
    creds = grpc.ssl_channel_credentials(root_certificates=root)
    return idm_pb2_grpc.IdmServiceStub(grpc.secure_channel(_target(), creds))


def validate_token(token: str):
    r = _stub().ValidateToken(idm_pb2.TokenRequest(token=token), timeout=5)
    return bool(r.valid), str(r.sub or ""), str(r.role or ""), str(r.email or ""), str(r.message or "")
