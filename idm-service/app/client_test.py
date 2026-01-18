import os
import grpc
from app import idm_pb2, idm_pb2_grpc

def main():
    target = os.getenv("IDM_TARGET", "idm-service:50051")

    with open(os.getenv("IDM_TLS_CERT"), "rb") as f:
        root_cert = f.read()

    creds = grpc.ssl_channel_credentials(root_certificates=root_cert)
    ch = grpc.secure_channel(target, creds)
    stub = idm_pb2_grpc.IdmServiceStub(ch)

    r = stub.Login(idm_pb2.LoginRequest(username="admin@test.com", password="admin123"))
    token = r.token
    print("TOKEN_OK", token[:30], bool(token))

    v0 = stub.ValidateToken(idm_pb2.TokenRequest(token=token))
    print("VALIDATE_NO_MD", v0.valid, v0.sub, v0.role, v0.message)

    try:
        stub.Logout(idm_pb2.TokenRequest(token=token))
        print("LOGOUT_NO_MD_UNEXPECTED_OK")
    except grpc.RpcError as e:
        print("LOGOUT_NO_MD", e.code().name, e.details())

    md = [("authorization", f"Bearer {token}")]

    v1 = stub.ValidateToken(idm_pb2.TokenRequest(token=token), metadata=md)
    print("VALIDATE_MD", v1.valid, v1.sub, v1.role, v1.message)

    lo = stub.Logout(idm_pb2.TokenRequest(token=token), metadata=md)
    print("LOGOUT_MD", lo.success, lo.message)

    v2 = stub.ValidateToken(idm_pb2.TokenRequest(token=token), metadata=md)
    print("VALIDATE_AFTER", v2.valid, v2.sub, v2.role, v2.message)

    bad = stub.ValidateToken(idm_pb2.TokenRequest(token="not-a-jwt"), metadata=md)
    print("VALIDATE_INVALID_TOKEN", bad.valid, bad.message)

if __name__ == "__main__":
    main()
