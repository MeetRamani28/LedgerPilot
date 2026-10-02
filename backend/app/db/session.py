from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import SQLModel
from app.core.config import settings

# Determine database URL based on provider
if settings.DB_PROVIDER == "postgres":
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
    )
else:
    # Default to SQLite
    db_url = settings.DATABASE_URL
    if not db_url.startswith("sqlite+aiosqlite://"):
        db_url = f"sqlite+aiosqlite:///{db_url.replace('sqlite:///', '').replace('sqlite://', '')}"
    engine = create_async_engine(
        db_url,
        echo=settings.DEBUG,
        future=True,
        connect_args={"check_same_thread": False},
    )

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    # Import models so SQLModel metadata registers all tables
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
