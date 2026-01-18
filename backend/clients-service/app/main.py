from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.clients import router as clients_router
from app.controllers.auth import router as auth_router


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

app.include_router(clients_router, tags=["clients"])
app.include_router(auth_router)

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
