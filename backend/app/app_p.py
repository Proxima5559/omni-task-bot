from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.bot.lifecycle import init_bot, close_bot
from app.config import settings
from app.database import engine
from app.redis_client import get_redis
from app.utils.errors import register_error_handlers
from app.utils.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    await init_bot(app)
    yield
    await close_bot(app)
    await get_redis().aclose()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    register_error_handlers(app)
    app.include_router(api_router) 
    
    return app

app = create_app()
