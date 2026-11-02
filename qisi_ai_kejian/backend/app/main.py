"""FastAPI entry — ask-teacher clarification + preview slice."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import ensure_db
from .routers import auth, catalog, sessions

app = FastAPI(
    title=settings.app_name,
    description="分享/追问老师 — clarification + 6-page preview (mock AI)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(sessions.router)


@app.on_event("startup")
def on_startup() -> None:
    ensure_db()


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "app": settings.app_name,
        "mock_mode": settings.mock_mode,
        "slice": "ask-teacher-preview",
    }
