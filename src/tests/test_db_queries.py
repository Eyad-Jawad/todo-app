from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from sqlalchemy.exc import IntegrityError, InvalidRequestError

from todo_app.db.models import Todo, User
from todo_app.db import context_session
from todo_app.db.queries import (
    add_todo,
    add_user,
    delete_todo,
    delete_user,
    get_todo,
    get_todos,
    get_user,
    revoke_token,
    add_refresh_token,
    get_refresh_token,
    is_refresh_token_valid,
    InvalidToken,
    toggle_todo,
)


@pytest.mark.asyncio
async def test_get_todos():
    async with context_session() as session:
        assert await get_todos(session, 1) == []
        await add_user(session, "TestUser1", "Anything")
        todo1 = await add_todo(session, 1, "Todo1")
        todo2 = await add_todo(session, 1, "Todo2")

        todos = list(await get_todos(session, 1))

        assert todos[0].todo_id == 1
        assert todos[0].todo_text == "Todo1"
        assert todos[0].is_done == False
        assert todos[0].user_id == 1
        assert todos[0].creation_date is not None
        assert todos[0] == todo1

        assert todos[1].todo_id == 2
        assert todos[1].todo_text == "Todo2"
        assert todos[1].is_done == False
        assert todos[1].user_id == 1
        assert todos[1].creation_date is not None
        assert todos[1] == todo2


@pytest.mark.asyncio
async def test_get_todo_with_existing_todo():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        await add_todo(session, 1, "Anything")

        todo = await get_todo(session, 1, 1)

    assert todo.todo_text == "Anything"
    assert todo.is_done == False
    assert todo.user_id == 1
    assert todo.creation_date is not None


@pytest.mark.asyncio
async def test_get_todo_with_no_todo():
    async with context_session() as session:
        todo = await get_todo(session, 1, 1)

    assert todo is None


@pytest.mark.asyncio
async def test_get_todo_with_no_user():
    with pytest.raises(IntegrityError):
        async with context_session() as session:
            user = await get_user(session, 1)
            assert user is None

            await add_todo(session, 1, "Anything")

            await get_todo(session, 1, 1)


@pytest.mark.asyncio
async def test_delete_with_existing_todo():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        todo = await add_todo(session, 1, "Anything")

        await delete_todo(session, todo)

        assert await get_todo(session, 1, 1) is None


@pytest.mark.asyncio
async def test_delete_with_non_existing_todo():
    with pytest.raises(InvalidRequestError):
        async with context_session() as session:
            todo = Todo(
                user_id=1,
                todo_text="str",
                is_done=False,
                creation_date=datetime.now(tz=UTC),
            )

            await delete_todo(session, todo)


@pytest.mark.asyncio
async def test_toggle():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        todo = await add_todo(session, 1, "Anything")

        await toggle_todo(session, todo)

        assert todo.is_done == True



@pytest.mark.asyncio
async def test_get_user_by_id_with_existing_user():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        user = await get_user(session, 1)

    assert user.id == 1
    assert user.username == "TestUser"
    assert user.hash == "Anything"


@pytest.mark.asyncio
async def test_get_user_by_id_with_non_existing_user():
    async with context_session() as session:
        user = await get_user(session, 1)

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_username_with_existing_user():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        user = await get_user(session, "TestUser")

    assert user.id == 1
    assert user.username == "TestUser"
    assert user.hash == "Anything"

@pytest.mark.asyncio
async def test_get_user_by_username_with_non_existing_user():
    async with context_session() as session:
        user = await get_user(session, "TestUser")

    assert user is None


@pytest.mark.asyncio
async def test_add_user_with_valid_input():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")

        user = await get_user(session, 1)

    assert user.id == 1
    assert user.username == "TestUser"
    assert user.hash == "Anything"


@pytest.mark.asyncio
async def test_add_user_with_duplicate_user():
    with pytest.raises(IntegrityError):
        async with context_session() as session:
            await add_user(session, "TestUser", "Anything")

            user = await get_user(session, 1)

            assert user.id == 1
            assert user.username == "TestUser"
            assert user.hash == "Anything"

            await add_user(session, "TestUser", "Anything")


@pytest.mark.asyncio
async def test_delete_user_with_new_user():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")

        user = await get_user(session, 1)

        await delete_user(session, user)

        user = await get_user(session, 1)
        assert user is None


@pytest.mark.asyncio
async def test_delete_user_with_user_with_relationships():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        await add_todo(session, 1, "Noice")
        await add_refresh_token(session, 1, "Token")

        user = await get_user(session, 1)

        await delete_user(session, user)

        user = await get_user(session, 1)
        todo = await get_todo(session, 1, 1)
        refresh_token = await get_refresh_token(session, "Token")

    assert user is None
    assert todo is None
    assert refresh_token is None


@pytest.mark.asyncio
async def test_add_refresh_token_with_existing_user():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        await add_refresh_token(session, 1, "Token")

        token = await get_refresh_token(session, "Token")

    assert token.expiration_date is not None
    assert token.is_valid
    assert token.user_id == 1


@pytest.mark.asyncio
async def test_add_refresh_token_with_non_existing_user():
    with pytest.raises(IntegrityError):
        async with context_session() as session:
            await add_refresh_token(session, 1, "Token")


@pytest.mark.asyncio
async def test_get_refresh_token_with_non_existing_token():
    async with context_session() as session:
        token = await get_refresh_token(session, "Token")
        assert token is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("is_valid"),
    [True, False],
)
async def test_validate_token_with_existing_token(is_valid):
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        await add_refresh_token(session, 1, "Token")

        token = await get_refresh_token(session, "Token")

        token.is_valid = is_valid

        assert await is_refresh_token_valid(session, "Token") == is_valid


@pytest.mark.asyncio
async def test_validate_token_with_non_existing_token():
    async with context_session() as session:
        assert await is_refresh_token_valid(session, "Token") == False


@pytest.mark.asyncio
async def test_revoke_token_with_revoked_token():
    with pytest.raises(InvalidToken):
        async with context_session() as session:
            await add_user(session, "TestUser", "Anything")
            await add_refresh_token(session, 1, "Token")

            token = await get_refresh_token(session, "Token")
            token.is_valid = False

            await revoke_token(session, "Token")


@pytest.mark.asyncio
async def test_revoke_token_with_non_existing_token():
    with pytest.raises(InvalidToken):
        async with context_session() as session:
            await revoke_token(session, "Token")


@pytest.mark.asyncio
async def test_revoke_token_with_existing_token():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        await add_refresh_token(session, 1, "Token")

        token = await get_refresh_token(session, "Token")

        await revoke_token(session, "Token")

        assert token.is_valid == False

@pytest.mark.asyncio
async def test_add_todo_with_existing_user():
    async with context_session() as session:
        await add_user(session, "TestUser", "Anything")
        todo = await add_todo(session, 1, "Todo")

    assert todo.user_id == 1
    assert todo.todo_text == "Todo"
    assert todo.creation_date is not None
    assert todo.is_done == False


@pytest.mark.asyncio
async def test_add_todo_with_non_existing_user():
    with pytest.raises(IntegrityError):
        async with context_session() as session:
            await add_todo(session, 1, "Todo")
