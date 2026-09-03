from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import pytest_asyncio

from todo_app.db.models import User
from todo_app.auth import (
    sign_up,
    login,
    log_out,
    delete_account,
    verify_password,
)


