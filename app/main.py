# 📁 app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import time

from app.core.config import settings
from app.core.database import engine
from app.core.logger import logger
from app.db.session import AsyncSessionLocal

# ── Import ALL models here so Base knows about them before create_all ─────────
from app.db.base import Base
from app.db.models.user import User, Role, Permission, RefreshToken  # noqa

# ── Import routers ─────────────────────────────────────────────────────────────
from app.routes.auth import router as auth_router


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📦 Environment : {settings.ENVIRONMENT}")

    # ✅ Test DB connection
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("🗄️  Database    : ✅ connected")
    except Exception as e:
        logger.error(f"🗄️  Database    : ❌ FAILED — {e}")
        raise RuntimeError(f"Cannot connect to database: {e}")

    # ✅ Auto-create all tables if they don't exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("📋 Tables      : ✅ ready")
    except Exception as e:
        logger.error(f"📋 Tables      : ❌ FAILED — {e}")
        raise RuntimeError(f"Cannot create tables: {e}")

    yield

    await engine.dispose()
    logger.info("👋 App shutdown complete")


# ── App instance ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 🔒 Tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"| status={response.status_code} "
        f"| {duration:.1f}ms"
    )
    return response


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(auth_router)


# ── Health Check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    db_status = "unreachable"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
    }


# ── Root ───────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }