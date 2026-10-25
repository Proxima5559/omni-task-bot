import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.redis_client import get_redis

log = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/tasks")
async def tasks_ws(ws: WebSocket) -> None:
    await ws.accept()
    pubsub = get_redis().pubsub()
    await pubsub.subscribe(settings.events_channel)

    async def forward() -> None:
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                await ws.send_text(msg["data"])

    async def watch_disconnect() -> None:
        while True:
            await ws.receive_text()  

    tasks = [asyncio.create_task(forward()), asyncio.create_task(watch_disconnect())]
    try:
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except WebSocketDisconnect:
        pass
    finally:
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await pubsub.unsubscribe(settings.events_channel)
        await pubsub.aclose()