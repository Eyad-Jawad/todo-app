from collections.abc import Sequence
from datetime import UTC, datetime
from typing import overload

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from todo_app.db.models import RefreshToken, Todo, User


class InvalidToken(ValueError):
    pass


async def get_todos(session: AsyncSession, user_id: int) -> Sequence[Todo]:
    stmt = select(Todo).where(Todo.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_todo(
    session: AsyncSession, user_id: int, todo_id: int
) -> Todo | None:
    stmt = select(Todo).where(Todo.user_id == user_id, Todo.todo_id == todo_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_todo(session: AsyncSession, user_id: int, text: str) -> Todo:
    todo = Todo(
        user_id=user_id,
        todo_text=text,
        creation_date=datetime.now(UTC),
        is_done=False,
    )

    session.add(todo)
    await session.commit()

    return todo


async def delete_todo(session: AsyncSession, todo: Todo) -> None:
    await session.delete(todo)
    await session.commit()


async def toggle_todo(session: AsyncSession, todo: Todo) -> None:
    todo.is_done = not todo.is_done
    await session.commit()


@overload
async def get_user(session: AsyncSession, identifier: int) -> User | None: ...


@overload
async def get_user(session: AsyncSession, identifier: str) -> User | None: ...


async def get_user(session: AsyncSession, identifier: int | str) -> User | None:
    pre_stmt = select(User).options(selectinload(User.todos))
    if isinstance(identifier, int):
        stmt = pre_stmt.where(User.id == identifier)
    else:
        stmt = pre_stmt.where(User.username == identifier)

    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_user(session: AsyncSession, username: str, hash: str) -> None:
    user = User(
        username=username,
        hash=hash,
    )

    session.add(user)
    await session.commit()


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()


async def add_refresh_token(
    session: AsyncSession, user_id: int, token: str
) -> RefreshToken:
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
    )

    session.add(refresh_token)
    await session.commit()

    return refresh_token


async def get_refresh_token(
    session: AsyncSession, token: str
) -> RefreshToken | None:
    result = await session.execute(
        select(RefreshToken).where(RefreshToken.token == token)
    )
    return result.scalar_one_or_none()


async def is_refresh_token_valid(session: AsyncSession, token: str) -> bool:
    refresh_token = await get_refresh_token(session, token)

    return bool(refresh_token and refresh_token.is_valid)


async def revoke_token(session: AsyncSession, token: str) -> None:
    refresh_token = await get_refresh_token(session, token)

    if refresh_token is None or not refresh_token.is_valid:
        raise InvalidToken("Token doesn't exist or already revoked")

    refresh_token.is_valid = False
