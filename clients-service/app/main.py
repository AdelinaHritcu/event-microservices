from contextlib import asynccontextmanager
from fastapi import FastAPI

from . import clients


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Optional: poti valida ca ai config corect / poti face un ping la mongo daca vrei
    yield


app = FastAPI(
    title="Clients Service API",
    lifespan=lifespan,
)

app.include_router(clients.router)


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
