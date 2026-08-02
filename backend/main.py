from fastapi import FastAPI
from backend.api.routes import auth, chat

app = FastAPI(title="Multi-Agent Research API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, tags=["chat"])
