import os
import sys
import grpc

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(THIS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import idm_pb2, idm_pb2_grpc


def load_root_cert() -> bytes:
    cert_path = os.getenv("IDM_CA_CERT", os.path.join(PROJECT_ROOT, "certs", "idm.crt"))
    with open(cert_path, "rb") as f:
        return f.read()


def md_bearer(token: str):
    return [("authorization", f"Bearer {token}")]


def main():
    target = os.getenv("IDM_TARGET", "localhost:50051")

    root_cert = load_root_cert()
    creds = grpc.ssl_channel_credentials(root_certificates=root_cert)
    ch = grpc.secure_channel(target, creds)
    stub = idm_pb2_grpc.IdmServiceStub(ch)

    print("\n== 1) LOGIN admin ==")
    admin_login = stub.Login(idm_pb2.LoginRequest(username="admin@test.com", password="admin123"))
    admin_token = admin_login.token
    print("admin_token_ok:", bool(admin_token), "prefix:", admin_token[:25])

    print("\n== 2) CREATE USER (admin only) ==")
    new_email = os.getenv("TEST_CREATE_EMAIL", "newclient@test.com")
    new_pass = os.getenv("TEST_CREATE_PASS", "pass123")
    new_role = os.getenv("TEST_CREATE_ROLE", "client")

    try:
        cu = stub.CreateUser(
            idm_pb2.CreateUserRequest(email=new_email, password=new_pass, role=new_role),
            metadata=md_bearer(admin_token),
        )
        print("create_user:", cu.success, cu.message, "sub:", cu.sub, "role:", cu.role)
    except grpc.RpcError as e:
        print("create_user_rpc_error:", e.code().name, e.details())

    print("\n== 3) LIST USERS (admin only) ==")
    try:
        lu = stub.ListUsers(idm_pb2.ListUsersRequest(), metadata=md_bearer(admin_token))
        for u in lu.users:
            print(" -", u.id, u.email, u.role)
    except grpc.RpcError as e:
        print("list_users_rpc_error:", e.code().name, e.details())

    print("\n== 4) LOGIN user created by admin ==")
    try:
        ulogin = stub.Login(idm_pb2.LoginRequest(username=new_email, password=new_pass))
        user_token = ulogin.token
        print("user_token_ok:", bool(user_token), "prefix:", user_token[:25])

        v = stub.ValidateToken(idm_pb2.TokenRequest(token=user_token))
        print("validate_user:", v.valid, v.sub, v.role, v.email, v.message)

        lo = stub.Logout(idm_pb2.TokenRequest(token=user_token), metadata=md_bearer(user_token))
        print("logout_user:", lo.success, lo.message)

        v2 = stub.ValidateToken(idm_pb2.TokenRequest(token=user_token))
        print("validate_after_logout:", v2.valid, v2.message)
    except grpc.RpcError as e:
        print("login/validate/logout rpc_error:", e.code().name, e.details())


if __name__ == "__main__":
    main()
