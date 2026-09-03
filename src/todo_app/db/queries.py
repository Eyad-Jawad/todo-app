from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from todo_app.db.models import Todo, User


async def get_todos(session: AsyncSession, user_id: int) -> Sequence[Todo]:
    stmt = select(Todo).where(Todo.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def add_todo(session: AsyncSession, user_id: int) -> None:
    text = input("Please input the todo text:\n")

    todo = Todo(
        user_id=user_id,
        todo_text=text,
        creation_date=datetime.now(tz=UTC),
        is_done=False,
    )

    session.add(todo)
    await session.commit()


async def delete_todo(session: AsyncSession, todo: Todo) -> None:
    await session.delete(todo)
    await session.commit()


async def toggle_todo(session: AsyncSession, todo: Todo) -> None:
    todo.is_done = not todo.is_done
    await session.commit()


async def get_user(username: str, session: AsyncSession) -> User | None:
    stmt = select(User).where(User.username == username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_session(
    access_token: str, session: AsyncSession
) -> User | None:
    stmt = select(User).where(User.access_token == access_token)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def add_uesr(session: AsyncSession, username: str, hash: str) -> str:
    access_token = str(uuid4())

    user = User(
        username=username,
        hash=hash,
        access_token=access_token,
    )

    session.add(user)
    await session.commit()

    return access_token


async def set_token(session: AsyncSession, user: User) -> str:
    access_token = str(uuid4())
    user.access_token = access_token
    await session.commit()

    return access_token


async def revoke_token(session: AsyncSession, user: User) -> None:
    user.access_token = None
    await session.commit()


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()
