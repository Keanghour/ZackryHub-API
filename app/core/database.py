# 📁 app/core/database.py

import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from app.core.config import settings

# SSL context required for Supabase pooler
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Create async engine
# ⚠️ statement_cache_size=0 is required for Supabase PgBouncer pooler
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    connect_args={
        "ssl": ssl_context,
        "statement_cache_size": 0,       # ✅ Fix for PgBouncer
        "prepared_statement_cache_size": 0,  # ✅ Fix for PgBouncer
    },
)