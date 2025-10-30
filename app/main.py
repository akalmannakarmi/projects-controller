from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.tasks import monitor_projects

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/ping", tags=["Ping"])
async def ping():
    return {"message": "pongasd"}


app.include_router(api_router, prefix=settings.API_V1_STR)


@asynccontextmanager
async def lifespan(_: FastAPI):
    thread = threading.Thread(target=monitor_projects, daemon=True)
    thread.start()
    yield


app.router.lifespan_context = lifespan
