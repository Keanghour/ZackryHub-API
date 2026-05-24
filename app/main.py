# 📁 app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from sqlalchemy import text
import traceback
import asyncio

from app.core import (
    settings, engine, logger, limiter,
    seed_roles_and_permissions,
    RequestMiddleware,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    rate_limit_exception_handler,
    global_exception_handler,
)
from app.db.session import AsyncSessionLocal

# ── Import ALL models ──────────────────────────────────────────────────────────
from app.db.base import Base
from app.db.models.user import User, Role, Permission, RefreshToken, PasswordResetToken  # noqa
from app.db.models.product import Product, Category  # noqa

# ── Import all routers ─────────────────────────────────────────────────────────
from app.routes import routes_controllers


# ── DB connection with retry ───────────────────────────────────────────────────
async def connect_with_retry(retries: int = 5, delay: int = 5) -> None:
    """Try to connect to DB, retry on failure."""
    for attempt in range(1, retries + 1):
        try:
            async with AsyncSessionLocal() as session:
                await session.execute(text("SELECT 1"))
            logger.info("🗄️  Database    : ✅ connected")
            return
        except Exception as e:
            logger.warning(
                f"🗄️  Database    : ⚠️  attempt {attempt}/{retries} failed — {str(e) or type(e).__name__}"
            )
            if attempt < retries:
                logger.info(f"   Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.error("🗄️  Database    : ❌ all retries exhausted")
                logger.error(traceback.format_exc())
                raise RuntimeError(
                    f"Cannot connect to database after {retries} attempts. "
                    f"Last error: {str(e) or type(e).__name__}"
                )


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"📦 Environment : {settings.ENVIRONMENT}")

    # 1️⃣ Connect to DB with retry
    await connect_with_retry(retries=5, delay=5)

    # 2️⃣ Auto-create tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("📋 Tables      : ✅ ready")
    except Exception as e:
        logger.error(f"📋 Tables      : ❌ FAILED — {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Cannot create tables: {str(e)}")

    # 3️⃣ Seed roles, permissions & super user
    try:
        async with AsyncSessionLocal() as session:
            await seed_roles_and_permissions(session)
    except Exception as e:
        logger.error(f"🌱 Seeder      : ❌ FAILED — {str(e)}")
        logger.error(traceback.format_exc())
        raise RuntimeError(f"Seeder failed: {str(e)}")

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
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# ── Middlewares ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestMiddleware)


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