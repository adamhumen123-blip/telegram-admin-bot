from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker | None = None


def init_engine(database_url: str) -> None:
    global engine, SessionLocal
    engine = create_async_engine(database_url, pool_pre_ping=True)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def create_tables() -> None:
    if engine is None:
        raise RuntimeError("Database engine is not initialized.")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_sessionmaker() -> async_sessionmaker:
    if SessionLocal is None:
        raise RuntimeError("Database sessionmaker is not initialized.")
    return SessionLocal
