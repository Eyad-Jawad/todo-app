from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


from todo_app.settings import settings

connect_args = {}

if settings.postgres_ssl == "true":
    connect_args["ssl"] = True

engine = create_async_engine(settings.db_url, connect_args=connect_args)


class Base(DeclarativeBase):
    pass


local_session = async_sessionmaker(bind=engine)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    try:
        session = local_session()
        yield session

    finally:
        await session.commit()
        await session.close()
