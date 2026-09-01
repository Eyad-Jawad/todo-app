from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

DB_PATH = Path(__file__).resolve().parent

engine = create_async_engine("sqlite+aiosqlite:///todo_app.db")


class Base(DeclarativeBase):
    pass


local_session = async_sessionmaker(bind=engine)


async def init_db() -> AsyncEngine:
    from . import models as models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        return engine


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    try:
        session = local_session()
        yield session

    finally:
        await session.commit()
        await session.close()
