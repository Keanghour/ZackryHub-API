# 📁 app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
import time

from app.core.config import settings
from app.core.database import engine
from app.core.logger import logger
from app.core.seeder import seed_roles_and_permissions
from app.db.session import AsyncSessionLocal

# ── Import ALL models so Base knows about them before create_all ──────────────
from app.db.base import Base
from app.db.models.user import User, Role, Permission, RefreshToken, PasswordResetToken  # noqa

# ── Import all routers ─────────────────────────────────────────────────────────
from app.routes import routes_controllers


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📦 Environment : {settings.ENVIRONMENT}")

    # 1️⃣ Test DB connection
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        logger.info("🗄️  Database    : ✅ connected")
    except Exception as e:
        logger.error(f"🗄️  Database    : ❌ FAILED — {e}")
        raise RuntimeError(f"Cannot connect to database: {e}")

    # 2️⃣ Auto-create all tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("📋 Tables      : ✅ ready")
    except Exception as e:
        logger.error(f"📋 Tables      : ❌ FAILED — {e}")
        raise RuntimeError(f"Cannot create tables: {e}")

    # 3️⃣ Seed roles & permissions
    try:
        async with AsyncSessionLocal() as session:
            await seed_roles_and_permissions(session)
    except Exception as e:
        logger.error(f"🌱 Seeder      : ❌ FAILED — {e}")
        raise RuntimeError(f"Seeder failed: {e}")

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
    allow_origins=["*"],
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


# ── Register all routers ───────────────────────────────────────────────────────
for router in routes_controllers:
    app.include_router(router)


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