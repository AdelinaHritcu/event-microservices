import os
from concurrent import futures

import grpc
import bcrypt
import jwt as pyjwt

from app import idm_pb2, idm_pb2_grpc
from app import db
from app.jwt_utils import issue_token, decode_and_verify
from app import token_blacklist
from app.auth_interceptor import AuthInterceptor


# demo accounts seeded by db.init_db(); passwords are hashed on first login
SEED_PASSWORDS = {
    "admin@test.com": os.getenv("IDM_SEED_ADMIN_PASS", "admin123"),
    "owner@test.com": os.getenv("IDM_SEED_OWNER_PASS", "owner123"),
    "client@test.com": os.getenv("IDM_SEED_CLIENT_PASS", "client123"),
}

# Lab 1 / 1.1.1: the administrator creates owner-event and client accounts
CREATABLE_ROLES = {"owner-event", "client"}


def _jwt_secret() -> str:
    return os.getenv("IDM_JWT_SECRET", "change_me")


def _jwt_alg() -> str:
    return os.getenv("IDM_JWT_ALG", "HS256")


class IdmService(idm_pb2_grpc.IdmServiceServicer):
    def Login(self, request, context):
        try:
            email = (request.username or "").strip()
            password = request.password or ""

            if not email or not password:
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, "username/password required")

            user = db.get_user_by_email(email)
            if not user:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid credentials")

            user_id, password_hash, role = user

            if password_hash == "TO_BE_SET":
                if email not in SEED_PASSWORDS:
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid credentials")
                hashed = bcrypt.hashpw(
                    SEED_PASSWORDS[email].encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
                db.set_password_hash_if_placeholder(email, hashed)
                password_hash = hashed

            if not bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8")):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid credentials")

            token = issue_token(user_id=user_id, role=role, email=email)
            return idm_pb2.LoginResponse(token=token)

        except grpc.RpcError:
            raise
        except Exception as e:
            context.abort(grpc.StatusCode.INTERNAL, f"Login crashed: {type(e).__name__}: {e}")

    def ValidateToken(self, request, context):
        """
        Lab 4 (b): the processing itself always succeeds; the response body says
        whether the token is valid. Expired / tampered tokens are blacklisted.
        """
        token = (request.token or "").strip()
        if not token:
            return idm_pb2.ValidateResponse(valid=False, message="missing")

        if token_blacklist.is_token_blacklisted(token):
            return idm_pb2.ValidateResponse(valid=False, message="blacklisted")

        try:
            payload = decode_and_verify(token)
        except pyjwt.ExpiredSignatureError:
            # signature is valid, only exp passed -> blacklist by jti
            try:
                payload = pyjwt.decode(
                    token, _jwt_secret(), algorithms=[_jwt_alg()],
                    options={"verify_exp": False},
                )
                token_blacklist.add(str(payload.get("jti", "")))
            except Exception:
                token_blacklist.add_token(token)
            return idm_pb2.ValidateResponse(valid=False, message="expired")
        except Exception:
            # integrity check failed: blacklist the token itself, never the jti it
            # claims (otherwise a forged token could revoke someone else's session)
            token_blacklist.add_token(token)
            return idm_pb2.ValidateResponse(valid=False, message="invalid")

        jti = str(payload.get("jti", ""))
        sub = str(payload.get("sub", ""))
        role = str(payload.get("role", ""))
        email = str(payload.get("email", ""))

        if not jti or not sub or not role:
            return idm_pb2.ValidateResponse(valid=False, message="invalid")

        if token_blacklist.is_blacklisted(jti):
            return idm_pb2.ValidateResponse(valid=False, message="blacklisted")

        return idm_pb2.ValidateResponse(valid=True, sub=sub, role=role, email=email, message="ok")

    def Logout(self, request, context):
        token = (request.token or "").strip()
        if not token:
            return idm_pb2.LogoutResponse(success=True, message="ok")
        try:
            payload = pyjwt.decode(
                token, _jwt_secret(), algorithms=[_jwt_alg()],
                options={"verify_exp": False},
            )
            token_blacklist.add(str(payload.get("jti", "")))
        except Exception:
            token_blacklist.add_token(token)
        return idm_pb2.LogoutResponse(success=True, message="ok")

    def CreateUser(self, request, context):
        email = (request.email or "").strip().lower()
        password = request.password or ""
        role = (request.role or "").strip()

        if not email or not password or not role:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "email/password/role required")
        if role not in CREATABLE_ROLES:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "role must be owner-event or client")

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user_id = db.create_user(email=email, password_hash=hashed, role=role)
        if not user_id:
            return idm_pb2.CreateUserResponse(success=False, message="email already exists")

        return idm_pb2.CreateUserResponse(success=True, message="created", sub=str(user_id), role=role)

    def ListUsers(self, request, context):
        users = [
            idm_pb2.User(id=str(u["id"]), email=u["email"], role=u["role"])
            for u in db.list_users()
        ]
        return idm_pb2.ListUsersResponse(users=users)

    def DeleteUser(self, request, context):
        try:
            uid = int(request.id)
        except (TypeError, ValueError):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "invalid id")
        if db.delete_user(uid):
            return idm_pb2.DeleteUserResponse(success=True, message="deleted")
        return idm_pb2.DeleteUserResponse(success=False, message="not found")


def build_server() -> grpc.Server:
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[AuthInterceptor()],
    )
    idm_pb2_grpc.add_IdmServiceServicer_to_server(IdmService(), server)
    return server


def serve():
    db.init_db()
    server = build_server()

    port = int(os.getenv("IDM_GRPC_PORT", "50051"))
    with open(os.getenv("IDM_TLS_CERT", "/certs/idm.crt"), "rb") as f:
        cert = f.read()
    with open(os.getenv("IDM_TLS_KEY", "/certs/idm.key"), "rb") as f:
        key = f.read()

    creds = grpc.ssl_server_credentials([(key, cert)])
    server.add_secure_port(f"[::]:{port}", creds)

    server.start()
    print(f"IDM gRPC server listening on :{port}", flush=True)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
