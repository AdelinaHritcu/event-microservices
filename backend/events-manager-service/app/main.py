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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
