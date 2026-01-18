from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.controllers.clients import router as clients_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(
    title="Clients Service API",
    lifespan=lifespan,
)
app.include_router(clients_router, tags=["clients"])

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "_links": {
            "self": {"href": "/"},
            "clients": {"href": "/api/clients"},
        }
    }
