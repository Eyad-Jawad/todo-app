from pathlib import Path
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


DB_PATH = Path(__file__).resolve().parent # todo-app/db

engine = create_async_engine(
    "sqlite+aiosqlite:///todo_app.db"
)

class Base(DeclarativeBase):
    pass

local_session = async_sessionmaker(bind=engine)

async def init_db() -> None:
    from . import models as models

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    finally:
        await engine.dispose()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession]:
    try:
        session = local_session()
        yield session

    finally:
        await session.commit()
        await session.close()
        