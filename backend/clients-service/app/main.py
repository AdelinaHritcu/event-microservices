from contextlib import asynccontextmanager

from fastapi import FastAPI
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
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
