import os
import grpc

from app import idm_pb2, idm_pb2_grpc


def _target() -> str:
    host = os.getenv("IDM_GRPC_HOST", "pos-idm-service")
    port = os.getenv("IDM_GRPC_PORT", "50051")
    return f"{host}:{port}"


def _channel() -> grpc.Channel:
    root_path = os.getenv("IDM_TLS_ROOT_CERT", "/certs/idm.crt")
    with open(root_path, "rb") as f:
        root = f.read()
    creds = grpc.ssl_channel_credentials(root_certificates=root)
    return grpc.secure_channel(_target(), creds)


def validate_token(token: str):
    ch = _channel()
    stub = idm_pb2_grpc.IdmServiceStub(ch)
    r = stub.ValidateToken(idm_pb2.TokenRequest(token=token))
    return bool(r.valid), str(r.sub or ""), str(r.role or ""), str(r.message or "")
