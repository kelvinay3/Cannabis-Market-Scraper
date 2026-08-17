import json
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import redis.asyncio as aioredis

from app.core.config import get_settings
from app.core.database import get_db, engine, Base
from app.api.routes import auth, users, dispensaries, deals, alerts, admin
from app.api.deps import get_current_user
from app.models.user import User

settings = get_settings()

redis_client: aioredis.Redis | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    global redis_client
    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

    async with engine.begin() as conn:
        # Tables managed by Alembic; only ensure PostGIS extension exists
        await conn.execute(__import__("sqlalchemy").text("CREATE EXTENSION IF NOT EXISTS postgis"))

    yield

    if redis_client:
        await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title="NJ Cannabis Market Intelligence",
    version="1.0.0",
    description="Real-time NJ dispensary deals, pricing, and menu tracker",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(dispensaries.router, prefix="/api")
app.include_router(deals.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, ws: WebSocket, channel: str):
        await ws.accept()
        self._connections.setdefault(channel, []).append(ws)

    def disconnect(self, ws: WebSocket, channel: str):
        if channel in self._connections:
            self._connections[channel] = [c for c in self._connections[channel] if c != ws]

    async def broadcast(self, channel: str, message: dict):
        dead = []
        for ws in self._connections.get(channel, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, channel)


manager = ConnectionManager()


@app.websocket("/ws/deals")
async def ws_deals(websocket: WebSocket):
    await manager.connect(websocket, "deals")
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, "deals")


@app.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket):
    await manager.connect(websocket, "prices")
    try:
        while True:
            await asyncio.sleep(30)
            await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, "prices")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/version")
async def version():
    return {"version": "1.0.0", "environment": settings.environment}
