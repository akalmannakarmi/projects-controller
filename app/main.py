from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME)


@app.get("/ping", tags=["Ping"])
async def ping():
    return {"message": "pong"}


app.include_router(api_router, prefix=settings.API_V1_STR)
