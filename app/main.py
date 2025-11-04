import logging
from contextlib import asynccontextmanager
import threading
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.tasks import monitor_projects

# ✅ Configure global logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(threadName)s - %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

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
    return {"message": "pong"}


app.include_router(api_router, prefix=settings.API_V1_STR)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("🚀 Starting background monitor thread...")
    thread = threading.Thread(
        target=monitor_projects, name="MonitorThread", daemon=True
    )
    thread.start()
    yield
    logger.info("🛑 Shutting down background monitor thread.")


app.router.lifespan_context = lifespan
