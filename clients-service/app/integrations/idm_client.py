import os
import grpc

from app import idm_pb2, idm_pb2_grpc


def _target() -> str:
    host = os.getenv("IDM_GRPC_HOST", "pos-idm-service")
    port = os.getenv("IDM_GRPC_PORT", "50051")
    return f"{host}:{port}"


def _creds() -> grpc.ChannelCredentials:
    cert_path = os.getenv("IDM_TLS_ROOT_CERT", "/certs/idm.crt")
    with open(cert_path, "rb") as f:
        root_cert = f.read()
    return grpc.ssl_channel_credentials(root_certificates=root_cert)


def _stub() -> idm_pb2_grpc.IdmServiceStub:
    ch = grpc.secure_channel(_target(), _creds())
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
