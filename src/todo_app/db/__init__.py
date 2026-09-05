import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = 5432

engine = create_async_engine(
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


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
