from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import event
from sqlalchemy.orm import DeclarativeBase


from todo_app.settings import settings

connect_args = {}

if settings.postgres_ssl == "true":
    connect_args["ssl"] = True

engine = create_async_engine(settings.db_url, connect_args=connect_args)

class Base(DeclarativeBase):
    pass


local_session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession]:
    session = local_session()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

@asynccontextmanager
async def context_session() -> AsyncGenerator[AsyncSession]:
    session = local_session()

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

@event.listens_for(engine.sync_engine, "connect")
def enable_foreign_key_enforcement(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
