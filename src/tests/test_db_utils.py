import pytest

from todo_app.db.models import Todo
from unittest.mock import MagicMock, patch, AsyncMock
from todo_app.db.utils import (
    get_todos,
    add_todo,
    delete_todo,
    toggle_todo,
)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()

    return session


@pytest.mark.asyncio
async def test_toggle(mock_session):
    todo = MagicMock()
    todo.is_done = False

    await toggle_todo(mock_session, todo)

    assert todo.is_done == True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete(mock_session):
    mock_session.delete = MagicMock()
    await delete_todo(mock_session, 1)

    mock_session.delete.assert_called_once_with(1)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("todo_app.db.utils.UTC", "val")
@patch("todo_app.db.utils.datetime")
@patch("builtins.input")
async def test_add_todo(mock_input, mock_time, mock_session):
    mock_input.return_value = "todo"
    mock_session.add = MagicMock()

    mock_time.now.return_value = 2

    await add_todo(1, mock_session)

    mock_input.assert_called_once()

    args, kwagrs = mock_session.add.call_args_list[0]
    todo = args[0]

    assert todo.user_id == 1
    assert todo.todo_text == "todo"
    assert todo.creation_date == 2
    assert todo.is_done == False

    mock_time.now.assert_called_once_with(tz="val")
    
    mock_session.commit.assert_awaited_once()
    


@pytest.mark.asyncio
@patch("todo_app.db.utils.select")
async def test_get_todos(mock_select, mock_session):
    stmt = MagicMock()
    mock_select.return_value.where.return_value = stmt


    todo = MagicMock()

    result = MagicMock()
    result.scalars.return_value.all.return_value = todo
    mock_session.execute.return_value = result

    assert await get_todos(mock_session, 2) == todo

    mock_select.assert_called_once_with(Todo)

    mock_session.execute.assert_awaited_once_with(stmt)

