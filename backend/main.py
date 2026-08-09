from fastapi import FastAPI
import redis.asyncio as redis
from backend.api.routes import auth, chat, reports
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):  # Get client on startup, close on shutdown
    app.state.redis_client = redis.from_url(
        os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
    )
    yield
    await app.state.redis_client.aclose()


app = FastAPI(title="Multi-Agent Research API", lifespan=lifespan)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, tags=["chat"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
