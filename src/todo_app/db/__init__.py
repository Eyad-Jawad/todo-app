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
DB_URL = os.environ["POSTGRES_URL"]

connect_args = {}

if os.environ.get("POSTGRES_SSL") == "true":
    connect_args["ssl"] = True

engine = create_async_engine(DB_URL, connect_args=connect_args)


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
