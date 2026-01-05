from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.controllers import events, packages, tickets
from app.database.init_mariadb import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Event Manager API",
    lifespan=lifespan
)

app.include_router(events.router)
app.include_router(packages.router)
app.include_router(tickets.router)


@app.get("/")
def root():
    return {
        "_links": {
            "self": {"href": "/"},
            "events": {"href": "/api/event-manager/events"},
            "packages": {"href": "/api/event-manager/event-packets"},
            "tickets": {"href": "/api/event-manager/tickets"},
            "clients": {"href": "/api/event-manager/clients"},
        }
    }
