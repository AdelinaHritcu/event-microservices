import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.clients import router as clients_router
from app.controllers.auth import router as auth_router
from app.controllers.users import router as users_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="Clients Service API",
    lifespan=lifespan,
)

def _cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    return [o.strip() for o in raw.split(",") if o.strip()]


# Lab 6 / 1.2: explicit origins, methods and headers. Authorization is not a
# "safe" header, so it must be listed for the browser to send it cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=False,  # the JWS travels in the Authorization header, not in cookies
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Lab 2: 415 when the representation is not conformant (wrong media type, body is
# not an object, a mandatory property is missing); 422 when it is conformant but
# some values are not admitted (e.g. invalid email, negative seats).
_STRUCTURE_ERRORS = {"missing", "model_attributes_type", "dict_type", "model_type", "json_invalid", "json_type"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    body_errors = [e for e in errors if (e.get("loc") or [None])[0] == "body"]
    content_type = request.headers.get("content-type", "")
    unsupported = bool(body_errors) and (
        not content_type.startswith("application/json")
        or any(e.get("type") in _STRUCTURE_ERRORS for e in body_errors)
    )
    return JSONResponse(
        status_code=415 if unsupported else 422,
        content={"detail": jsonable_encoder(errors)},
    )


app.include_router(auth_router)
app.include_router(users_router)
app.include_router(clients_router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {
        "_links": {
            "self": {"href": "/", "type": "GET"},
            "login": {"href": "/auth/login", "type": "POST"},
            "logout": {"href": "/auth/logout", "type": "POST"},
            "me": {"href": "/auth/me", "type": "GET"},
            "clients": {"href": "/api/clients", "type": "GET"},
            "my-profile": {"href": "/api/clients/me", "type": "GET"},
            "my-tickets": {"href": "/api/clients/me/tickets", "type": "GET"},
            "buyers": {"href": "/api/clients/buyers", "type": "GET"},
            "users": {"href": "/api/users", "type": "GET"},
            "openapi": {"href": "/openapi.json", "type": "GET"},
        }
    }
