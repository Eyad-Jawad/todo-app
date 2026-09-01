from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from todo_app.db.models import Todo


async def get_todos(session: AsyncSession, user_id: int) -> Sequence[Todo]:
    stmt = select(Todo).where(Todo.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def add_todo(user_id: int, session: AsyncSession) -> None:
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
