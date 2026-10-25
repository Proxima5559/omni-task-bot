from fastapi import APIRouter
from app.api import bot as bot_api
from app.api import tasks as tasks_api
from app.api import ws as ws_api
from app.database import engine
from app.redis_client import get_redis
from sqlalchemy import text

api_router = APIRouter()

api_router.include_router(tasks_api.router)
api_router.include_router(ws_api.router)
api_router.include_router(bot_api.router)

@api_router.get("/health", tags=["meta"])
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    await get_redis().ping()
    return {"status": "ok"}
