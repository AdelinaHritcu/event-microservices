from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.controllers import events as events_controller
from app.controllers import packages as packages_controller
from app.controllers import tickets as tickets_controller
from app.database.init_mariadb import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Event Manager API",
    lifespan=lifespan,
)

app.include_router(events_controller.router)
app.include_router(packages_controller.router)
app.include_router(tickets_controller.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "_links": {
            "self": {"href": "/api/event-manager/"},
            "events": {"href": "/api/event-manager/events"},
            "packages": {"href": "/api/event-manager/event-packets"},
            "tickets": {"href": "/api/event-manager/tickets"},
        }
    }
