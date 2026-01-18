import os
import time
import uuid
import jwt as pyjwt

def issue_token(user_id: int, role: str, email: str) -> str:
    secret = os.getenv("IDM_JWT_SECRET", "change_me")
    alg = os.getenv("IDM_JWT_ALG", "HS256")
    issuer = os.getenv("IDM_JWT_ISSUER", "pos-idm")

    now = int(time.time())
    exp = now + int(os.getenv("IDM_JWT_TTL_SECONDS", "900"))

    payload = {
        "iss": issuer,
        "sub": str(user_id),
        "role": role,
        "email": email,
        "iat": now,
        "exp": exp,
        "jti": str(uuid.uuid4()),
    }

    return pyjwt.encode(payload, secret, algorithm=alg)

def decode_and_verify(token: str) -> dict:
    secret = os.getenv("IDM_JWT_SECRET", "change_me")
    alg = os.getenv("IDM_JWT_ALG", "HS256")
    issuer = os.getenv("IDM_JWT_ISSUER", "pos-idm")

    payload = pyjwt.decode(
        token,
        secret,
        algorithms=[alg],
        options={"require": ["exp", "sub", "role", "jti", "iss"]},
    )

    if payload.get("iss") != issuer:
        raise pyjwt.InvalidIssuerError("invalid issuer")

    return payload
