# 📁 app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.core import routes_cores, logger
from app.db.session import AsyncSessionLocal

# ── Import ALL models ──────────────────────────────────────────────────────────
from app.db.base import Base
from app.db.models.user import User, Role, Permission, RefreshToken, PasswordResetToken  # noqa

# ── Import all routers ─────────────────────────────────────────────────────────
from app.routes import routes_controllers

# ── Unpack core dependencies ───────────────────────────────────────────────────
settings    = routes_cores["settings"]
engine      = routes_cores["engine"]
limiter     = routes_cores["limiter"]
seed        = routes_cores["seed"]
exc         = routes_cores["exception_handlers"]


# ── Lifespan ───────────────────────────────────────────────────────────────────
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

    # 2️⃣ Auto-create tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("📋 Tables      : ✅ ready")
    except Exception as e:
        logger.error(f"📋 Tables      : ❌ FAILED — {e}")
        raise RuntimeError(f"Cannot create tables: {e}")

    # 3️⃣ Seed roles, permissions & super user
    try:
        async with AsyncSessionLocal() as session:
            await seed(session)
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

# ── Rate limiter state ─────────────────────────────────────────────────────────
app.state.limiter = limiter

# ── Exception handlers ─────────────────────────────────────────────────────────
app.add_exception_handler(RequestValidationError, exc["validation"])
app.add_exception_handler(SQLAlchemyError,        exc["sqlalchemy"])
app.add_exception_handler(RateLimitExceeded,      exc["rate_limit"])
app.add_exception_handler(Exception,              exc["global"])

# ── Middlewares ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(routes_cores["middleware"])


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