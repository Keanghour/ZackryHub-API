from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from app.core.database import engine

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # Keep objects usable after commit
    autocommit=False,
    autoflush=False,
)


# Dependency — use this in your routes
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()