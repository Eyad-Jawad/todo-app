from datetime import UTC, datetime
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from todo_app.db.models import Todo, User
from todo_app.db.queries import (
    add_todo,
    add_user,
    delete_todo,
    delete_user,
    get_todos,
    get_user,
    get_user_session,
    revoke_token,
    set_token,
    toggle_todo,
)


@pytest_asyncio.fixture
async def mock_session():

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    local_session = async_sessionmaker(bind=engine)
    session = local_session()

    from todo_app.db import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        yield session
        await session.close()

    await engine.dispose()


@pytest.mark.asyncio
async def test_toggle(mock_session):
    todo = Todo(
        user_id=1,
        todo_text="str",
        is_done=False,
        creation_date=datetime.now(tz=UTC),
    )
    mock_session.add(todo)
    await mock_session.commit()

    stmt = select(Todo)
    result = await mock_session.execute(stmt)
    todo = result.scalar_one()

    await toggle_todo(mock_session, todo)

    stmt = select(Todo)
    result = await mock_session.execute(stmt)
    todo = result.scalar_one()

    assert todo.is_done == True


@pytest.mark.asyncio
async def test_delete(mock_session):
    todo = Todo(
        user_id=1,
        todo_text="str",
        is_done=True,
        creation_date=datetime.now(tz=UTC),
    )
    mock_session.add(todo)
    await mock_session.commit()

    stmt = select(Todo)
    result = await mock_session.execute(stmt)
    todo = result.scalar_one()

    await delete_todo(mock_session, todo)

    stmt = select(Todo)
    result = await mock_session.execute(stmt)
    result_todo = result.scalar_one_or_none()

    assert result_todo is None


@pytest.mark.asyncio
@patch("todo_app.db.queries.UTC", "val")
@patch("todo_app.db.queries.datetime")
async def test_add_todo(mock_time, mock_session):
    date = datetime.now(tz=UTC)
    mock_time.now.return_value = date

    await add_todo(mock_session, 1, "str")

    stmt = select(Todo)
    result = await mock_session.execute(stmt)
    todo = result.scalar_one()

    assert todo.user_id == 1
    assert todo.todo_text == "str"
    assert todo.creation_date == date.replace(tzinfo=None)
    assert todo.is_done == False

    mock_time.now.assert_called_once_with(tz="val")


@pytest.mark.asyncio
async def test_get_todos(mock_session):
    todos = [
        Todo(
            user_id=2,
            todo_text="str",
            is_done=True,
            creation_date=datetime.now(tz=UTC),
        ),
        Todo(
            user_id=2,
            todo_text="str2",
            is_done=False,
            creation_date=datetime.now(tz=UTC),
        ),
    ]

    mock_session.add(todos[0])
    mock_session.add(todos[1])
    await mock_session.commit()

    assert list(await get_todos(mock_session, 2)) == todos


@pytest.mark.asyncio
async def test_get_user_with_no_entry(mock_session):
    assert await get_user(mock_session, "rand") is None


@pytest.mark.asyncio
async def test_get_user_with_one_entry(mock_session):
    mock_session.add(
        User(
            username="Noice",
            hash="Anything",
        )
    )
    await mock_session.commit()

    user = await get_user(mock_session, "Noice")

    assert user.username == "Noice"
    assert user.hash == "Anything"


@pytest.mark.asyncio
async def test_get_user_sesison_with_no_entry(mock_session):
    assert await get_user_session(mock_session, "") is None


@pytest.mark.asyncio
async def test_get_user_sesison_with_empty_entry(mock_session):
    mock_session.add(
        User(
            username="Noice",
            hash="Anything",
        )
    )

    assert await get_user_session(mock_session, "") is None


@pytest.mark.asyncio
async def test_get_user_sesison_with_one_entry(mock_session):
    mock_session.add(User(username="Noice", hash="Anything", access_token="T"))

    user = await get_user_session(mock_session, "T")

    assert user.username == "Noice"
    assert user.hash == "Anything"
    assert user.access_token == "T"


@pytest.mark.asyncio
@patch("todo_app.db.queries.uuid4")
async def test_add_user(mock_uuid, mock_session):
    mock_uuid.return_value = "token"

    assert await add_user(mock_session, "Noice", "Anything") == "token"

    stmt = select(User)
    result = await mock_session.execute(stmt)
    user = result.scalar_one()

    assert user.username == "Noice"
    assert user.hash == "Anything"
    assert user.access_token == "token"


@pytest.mark.asyncio
@patch("todo_app.db.queries.uuid4")
async def test_set_token_empty(mock_uuid, mock_session):
    mock_uuid.return_value = "token"

    user = User(
        username="Noice",
        hash="Anything",
    )
    mock_session.add(user)
    await mock_session.commit()

    assert await set_token(mock_session, user) == "token"

    stmt = select(User)
    result = await mock_session.execute(stmt)
    user = result.scalar_one()

    assert user.username == "Noice"
    assert user.hash == "Anything"
    assert user.access_token == "token"


@pytest.mark.asyncio
@patch("todo_app.db.queries.uuid4")
async def test_set_token_overwrite(mock_uuid, mock_session):
    mock_uuid.return_value = "token"

    user = User(
        username="Noice",
        hash="Anything",
        access_token="T",
    )
    mock_session.add(user)
    await mock_session.commit()

    assert await set_token(mock_session, user) == "token"

    stmt = select(User)
    result = await mock_session.execute(stmt)
    user = result.scalar_one()

    assert user.username == "Noice"
    assert user.hash == "Anything"
    assert user.access_token == "token"


@pytest.mark.asyncio
async def test_revoke_token(mock_session):
    user = User(
        username="Noice",
        hash="Anything",
        access_token="T",
    )
    mock_session.add(user)
    await mock_session.commit()

    await revoke_token(mock_session, user)

    stmt = select(User)
    result = await mock_session.execute(stmt)
    user = result.scalar_one()

    assert user.username == "Noice"
    assert user.hash == "Anything"
    assert user.access_token == None


@pytest.mark.asyncio
async def test_delete_user(mock_session):
    user = User(
        username="Noice",
        hash="Anything",
        access_token="T",
    )

    mock_session.add(user)
    await mock_session.commit()

    stmt = select(User)
    result = await mock_session.execute(stmt)
    user = result.scalar_one_or_none()

    todo = Todo(
        user_id=user.id,
        todo_text="meh",
        is_done=False,
        creation_date=datetime.now(tz=UTC),
    )

    mock_session.add(todo)
    await mock_session.commit()

    await delete_user(mock_session, user)

    stmt = select(User)
    result = await mock_session.execute(stmt)
    user = result.scalar_one_or_none()

    stmt = select(Todo)
    result = await mock_session.execute(stmt)
    todo = result.scalar_one_or_none()

    assert user is None
    assert todo is None
