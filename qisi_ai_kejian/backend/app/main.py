"""FastAPI entry — ask-teacher clarification + preview slice."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import ensure_db
from .admin.router import router as admin_router
from .routers import auth, catalog, membership, pay, sessions
from .routers import generate

app = FastAPI(
    title=settings.app_name,
    description="奇思 AI 课件 — ask-teacher + generate + membership + admin (mock)",
    version="0.3.0",
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
app.include_router(generate.router)
app.include_router(generate.artifacts_router)
app.include_router(membership.router)
app.include_router(pay.router)
app.include_router(admin_router)


@app.on_event("startup")
def on_startup() -> None:
    ensure_db()


@app.get("/api/health")
def health() -> dict:
    return {
        "ok": True,
        "app": settings.app_name,
        "mock_mode": settings.mock_mode,
        "slice": "full-product-mock",
        "admin": "/admin/members",
    }
