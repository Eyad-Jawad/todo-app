import readchar

from textwrap import dedent
from datetime import datetime, UTC

from rich.console import Console
from sqlalchemy import select, delete, insert
from sqlalchemy.ext.asyncio import AsyncSession
from todo_app.db import init_db, get_session
from todo_app.db.models import Todo

async def interface(user_id: int = 0):
    await init_db()

    async with get_session() as session:
        console = Console()
        current_line = 0
        todos = await get_todos(session, user_id)

        console.print(format_todos(todos, current_line, console))

        while True:
            key = readchar.readkey()

            if key == readchar.key.ENTER:
                todos[current_line].is_done = True if not todos[current_line].is_done else False
            elif key == readchar.key.DOWN:
                current_line = handle_value_changing(current_line, 1, len(todos))
            elif key == readchar.key.UP:
                current_line = handle_value_changing(current_line, -1, len(todos))
            elif key.lower() == "a":
                await add_todo(user_id, session)
            elif key.lower() == "d":
                await delete_todo(session, todos[current_line])
            elif key.lower() == "q":
                console.clear()
                break
            else: 
                continue

            todos = await get_todos(session, user_id)
            console.clear()
            console.print(format_todos(todos, current_line, console))


def format_todos(todos: list[Todo], current_line: int, console: Console) -> str:
    CONTROLS_STR = dedent("""
        Press:
            [cyan](Enter)[/] to toggle the todo
            [cyan](A)[/]dd to add a new todo
            [red](D)[/]elete to delete a highlighted todo
            [red](Q)[/]uit to quit the app
    """)

    EMPTY_LIST_STR = dedent("""
        You currently have no todo, press:
            [cyan](A)[/]dd to add a new todo
            [red](Q)[/]uit to quit the app
    """)

    SMALL_TERMINAL_STR = "Terminal too small to show anything"

    if len(todos) == 0:
        if is_str_fit_terminal(EMPTY_LIST_STR, console):
            return EMPTY_LIST_STR

        return SMALL_TERMINAL_STR

    if console.height <= 5:
        return SMALL_TERMINAL_STR

    if not is_str_fit_terminal(CONTROLS_STR, console):
        return SMALL_TERMINAL_STR

    window = select_window(todos, current_line, console.height - 5)

    s = "\n".join(window)
    return f"{CONTROLS_STR}\n{s}"


def select_window(todos: list[Todo], current_idx: int, window_length: int) -> list[str]:
    EMPTY_SQUARE = "□"
    FILLED_SQUARE = "■"

    n = len(todos)

    if n <= window_length:
        result = []
        for i, todo in enumerate(todos):
            is_done = FILLED_SQUARE if todo.is_done else EMPTY_SQUARE

            if i == current_idx:
                result.append(f"> {is_done} [bold black on cyan]{todo.todo_text}[/]")
            else:
                result.append(f"  {is_done} {todo.todo_text}")

        return result


    offset = window_length // 2

    result = []

    for i in range(-offset, ):
        idx = (current_idx + i) % n
        is_done = FILLED_SQUARE if todos[idx].is_done else EMPTY_SQUARE
        result.append(f"  {is_done} {todos[idx].todo_text}")

    is_done = FILLED_SQUARE if todos[current_idx].is_done else EMPTY_SQUARE
    result.append(f"> {is_done} [bold black on cyan]{todos[current_idx].todo_text}[/]")

    for i in range(1, offset + 1):
        idx = (current_idx + i) % n
        is_done = FILLED_SQUARE if todos[idx].is_done else EMPTY_SQUARE
        result.append(f"  {is_done} {todos[idx].todo_text}")

    return result


def is_str_fit_terminal(s: str, console: Console) -> bool:
    if console.height < s.count('\n'):
        return False

    console_size = console.height * console.size.width

    return len(s) < console_size


def handle_value_changing(value: int, add: int, length: int) -> int:
    if add < -1: add = -1
    elif add >= 0: add = 1

    if value + add == length:
        return 0

    if value + add < 0:
        return length - 1

    return value + add


async def get_todos(session: AsyncSession, user_id: int) -> list[Todo]:
    stmt = select(Todo).where(Todo.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def add_todo(user_id: int, session: AsyncSession) -> None:
    text = input("Please input the todo text:\n")

    stmt = insert(Todo).values(
        user_id=user_id, 
        todo_text=text, 
        creation_date=datetime.now(tz=UTC), 
        is_done=False,
    )
    await session.execute(stmt)
    await session.commit()


async def delete_todo(session: AsyncSession, todo: Todo) -> None:
    stmt = delete(Todo).where(Todo.todo_id == todo.todo_id)
    await session.execute(stmt)
    await session.commit()
