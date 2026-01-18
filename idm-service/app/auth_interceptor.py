from __future__ import annotations

import grpc
from typing import Callable, Iterable, Optional, Tuple

from app.jwt_utils import decode_and_verify
from app import token_blacklist

Metadata = Iterable[Tuple[str, str]]

def _get_auth_header(md: Metadata) -> Optional[str]:
    for k, v in md:
        if k.lower() == "authorization":
            return v
    return None

def _extract_bearer_token(auth_header: str) -> Optional[str]:
    if not auth_header:
        return None
    parts = auth_header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1].strip()
    return None

class AuthInterceptor(grpc.ServerInterceptor):
    PUBLIC_METHODS = {
        "/idm.IdmService/Login",
        "/idm.IdmService/ValidateToken",
    }

    ROLE_RULES = {
        "/idm.IdmService/Logout": {"admin", "owner-event", "client"},
    }

    def intercept_service(self, continuation: Callable, handler_call_details: grpc.HandlerCallDetails):
        method = handler_call_details.method

        handler = continuation(handler_call_details)
        if handler is None:
            return None

        if method in self.PUBLIC_METHODS:
            return handler

        def unary_unary(request, context: grpc.ServicerContext):
            md = handler_call_details.invocation_metadata or ()
            auth = _get_auth_header(md)
            token = _extract_bearer_token(auth or "")

            if not token:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "missing bearer token")

            try:
                payload = decode_and_verify(token)
            except Exception:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid token")

            jti = str(payload.get("jti", ""))
            role = str(payload.get("role", ""))

            if token_blacklist.is_blacklisted(jti):
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "token revoked")

            allowed_roles = self.ROLE_RULES.get(method)
            if allowed_roles is not None and role not in allowed_roles:
                context.abort(grpc.StatusCode.PERMISSION_DENIED, "insufficient privileges")

            return handler.unary_unary(request, context)

        return grpc.unary_unary_rpc_method_handler(
            unary_unary,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
