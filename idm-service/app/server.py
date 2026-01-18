import os
from concurrent import futures

import grpc
import bcrypt
import jwt as pyjwt

from app import idm_pb2, idm_pb2_grpc
from app.db import init_db, get_user_by_email, set_password_hash_if_placeholder
from app.jwt_utils import issue_token, decode_and_verify
from app import token_blacklist
from app.auth_interceptor import AuthInterceptor


SEED_PASSWORDS = {
    "admin@test.com": "admin123",
    "owner@test.com": "owner123",
    "client@test.com": "client123",
}


class IdmService(idm_pb2_grpc.IdmServiceServicer):
    def Login(self, request, context):
        email = (request.username or "").strip()
        password = request.password or ""

        if not email or not password:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "username/password required")

        user = get_user_by_email(email)
        if not user:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid credentials")

        user_id, password_hash, role = user

        if password_hash == "TO_BE_SET":
            if email not in SEED_PASSWORDS:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid credentials")

            hashed = bcrypt.hashpw(
                SEED_PASSWORDS[email].encode("utf-8"),
                bcrypt.gensalt()
            ).decode("utf-8")
            set_password_hash_if_placeholder(email, hashed)
            password_hash = hashed

        try:
            ok = bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except Exception:
            ok = False

        if not ok:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid credentials")

        token = issue_token(user_id=user_id, role=role, email=email)
        return idm_pb2.LoginResponse(token=token)

    def ValidateToken(self, request, context):
        token = (request.token or "").strip()
        if not token:
            return idm_pb2.ValidateResponse(valid=False, sub="", role="", message="missing")

        try:
            payload = decode_and_verify(token)

            jti = str(payload.get("jti", ""))
            sub = str(payload.get("sub", ""))
            role = str(payload.get("role", ""))

            if not jti or not sub or not role:
                return idm_pb2.ValidateResponse(valid=False, sub="", role="", message="invalid")

            if token_blacklist.is_blacklisted(jti):
                return idm_pb2.ValidateResponse(valid=False, sub="", role="", message="blacklisted")

            return idm_pb2.ValidateResponse(valid=True, sub=sub, role=role, message="ok")

        except pyjwt.ExpiredSignatureError:
            try:
                payload = pyjwt.decode(
                    token,
                    os.getenv("IDM_JWT_SECRET", "change_me"),
                    algorithms=[os.getenv("IDM_JWT_ALG", "HS256")],
                    options={"verify_exp": False}
                )
                jti = str(payload.get("jti", ""))
                token_blacklist.add(jti)
            except Exception:
                pass

            return idm_pb2.ValidateResponse(valid=False, sub="", role="", message="expired")

        except Exception:
            try:
                payload = pyjwt.decode(
                    token,
                    os.getenv("IDM_JWT_SECRET", "change_me"),
                    algorithms=[os.getenv("IDM_JWT_ALG", "HS256")],
                    options={"verify_signature": False, "verify_exp": False}
                )
                jti = str(payload.get("jti", ""))
                token_blacklist.add(jti)
            except Exception:
                pass

            return idm_pb2.ValidateResponse(valid=False, sub="", role="", message="invalid")

    def Logout(self, request, context):
        token = (request.token or "").strip()
        if not token:
            return idm_pb2.LogoutResponse(success=True, message="ok")

        try:
            payload = pyjwt.decode(
                token,
                os.getenv("IDM_JWT_SECRET", "change_me"),
                algorithms=[os.getenv("IDM_JWT_ALG", "HS256")],
                options={"verify_exp": False}
            )
            jti = str(payload.get("jti", ""))
            token_blacklist.add(jti)
        except Exception:
            pass

        return idm_pb2.LogoutResponse(success=True, message="ok")


def serve():
    init_db()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        interceptors=[AuthInterceptor()],
    )
    idm_pb2_grpc.add_IdmServiceServicer_to_server(IdmService(), server)

    port = int(os.getenv("IDM_GRPC_PORT", "50051"))

    with open(os.getenv("IDM_TLS_CERT"), "rb") as f:
        cert = f.read()
    with open(os.getenv("IDM_TLS_KEY"), "rb") as f:
        key = f.read()

    creds = grpc.ssl_server_credentials([(key, cert)])
    server.add_secure_port(f"[::]:{port}", creds)

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
