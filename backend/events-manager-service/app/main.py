import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.controllers import events as events_controller
from app.controllers import packages as packages_controller
from app.controllers import tickets as tickets_controller
from app.database.init_mariadb import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.links import client_links

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Event Manager API",
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

app.include_router(events_controller.router)
app.include_router(packages_controller.router)
app.include_router(tickets_controller.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
@app.get("/api/event-manager")
def root():
    return {
        "_links": {
            "self": {"href": "/api/event-manager", "type": "GET"},
            "events": {"href": "/api/event-manager/events", "type": "GET"},
            "event-packets": {"href": "/api/event-manager/event-packets", "type": "GET"},
            "tickets": {"href": "/api/event-manager/tickets", "type": "GET"},
            "openapi": {"href": "/openapi.json", "type": "GET"},
            **client_links(),
        }
    }
