from fastapi import FastAPI

from backend.api.routes import auth, chat, reports

app = FastAPI(title="Multi-Agent Research API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(chat.router, tags=["chat"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
