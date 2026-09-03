from unittest.mock import AsyncMock, MagicMock

import pytest


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
