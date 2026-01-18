import os
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


def _stub() -> idm_pb2_grpc.IdmServiceStub:
    if _use_tls():
        ch = grpc.secure_channel(_target(), _creds())
    else:
        ch = grpc.insecure_channel(_target())
    return idm_pb2_grpc.IdmServiceStub(ch)


def login(username: str, password: str) -> str:
    stub = _stub()
    r = stub.Login(idm_pb2.LoginRequest(username=username, password=password))
    return r.token


def validate_token(token: str):
    stub = _stub()
    r = stub.ValidateToken(idm_pb2.TokenRequest(token=token))
    return r.valid, r.sub, r.role, r.message


def logout(token: str):
    stub = _stub()
    md = [("authorization", f"Bearer {token}")]
    r = stub.Logout(idm_pb2.TokenRequest(token=token), metadata=md)
    return r.success, r.message
