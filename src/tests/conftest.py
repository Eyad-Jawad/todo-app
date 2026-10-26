from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from todo_app.services import app
from todo_app.services.auth import auth_rate_limiter
from todo_app.services.todo import todo_rate_limiter


def no_rate_limit():
    pass

app.dependency_overrides[auth_rate_limiter] = no_rate_limit
app.dependency_overrides[todo_rate_limiter] = no_rate_limit


class AsyncContextManager:
    async def __aenter__(self, *args, **kwargs):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass


@pytest.fixture
def mock_with_session():
    session = MagicMock()

    instance = AsyncContextManager()
    instance.__aenter__ = AsyncMock(return_value=session)

    return instance


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    from todo_app.db import Base, engine
    from todo_app.db import models as models

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

