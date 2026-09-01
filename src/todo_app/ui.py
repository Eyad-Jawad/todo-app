from collections.abc import Sequence
from enum import Enum, auto
from textwrap import dedent

import readchar
from rich.console import Console
from sqlalchemy.ext.asyncio import AsyncSession

from todo_app.db import get_session, init_db
from todo_app.db.models import Todo
from todo_app.db.utils import (
    add_todo,
    delete_todo,
    get_todos,
    toggle_todo,
)


class KeyAction(Enum):
    NOTHING = auto()
    DB_CHANGED = auto()
    LINE_CHANGED = auto()
    QUIT = auto()


CONTROLS_STR = dedent("""
    Press:
        [cyan](Enter)[/] to toggle the todo
        [cyan](A)[/]dd to add a new todo
        [cyan]Arrow keys[/] to navigate the todos
        [red](D)[/]elete to delete a highlighted todo
        [red](Q)[/]uit to quit the app
""")

EMPTY_LIST_STR = dedent("""
    You currently have no todo, press:
        [cyan](A)[/]dd to add a new todo
        [red](Q)[/]uit to quit the app
""")

SMALL_TERMINAL_STR = "Terminal too small to show anything"

EMPTY_SQUARE = "□"
FILLED_SQUARE = "■"


async def interface(user_id: int = 0) -> None:
    await init_db()

    async with get_session() as session:
        console = Console()
        current_line = 0
        todos = await get_todos(session, user_id)

        console.print(format_todos(todos, current_line, console))
        await key_event_handler(session, console, user_id, todos, current_line)


async def key_event_handler(
    session: AsyncSession,
    console: Console,
    user_id: int,
    todos: Sequence[Todo],
    current_line: int,
) -> None:
    while True:
        current_line, action = await handle_keys(
            todos, current_line, session, user_id
        )
        if action == KeyAction.QUIT:
            console.clear()
            break
        elif action == KeyAction.DB_CHANGED:
            todos = await get_todos(session, user_id)
        elif action == KeyAction.NOTHING:
            continue

        console.clear()
        console.print(format_todos(todos, current_line, console))


async def handle_keys(
    todos: Sequence[Todo],
    current_line: int,
    session: AsyncSession,
    user_id: int,
) -> tuple[int, KeyAction]:
    key = readchar.readkey()

    if key == readchar.key.ENTER:
        await toggle_todo(session, todos[current_line])
        return current_line, KeyAction.DB_CHANGED
    elif key == readchar.key.DOWN:
        current_line = move_cursor(current_line, 1, len(todos))
        return current_line, KeyAction.LINE_CHANGED
    elif key == readchar.key.UP:
        current_line = move_cursor(current_line, -1, len(todos))
        return current_line, KeyAction.LINE_CHANGED
    elif key.lower() == "a":
        await add_todo(user_id, session)
        return current_line, KeyAction.DB_CHANGED
    elif key.lower() == "d":
        await delete_todo(session, todos[current_line])
        return current_line - 1, KeyAction.DB_CHANGED
    elif key.lower() == "q":
        return 0, KeyAction.QUIT
    else:
        return current_line, KeyAction.NOTHING


def format_todos(
    todos: Sequence[Todo], current_line: int, console: Console
) -> str:
    if len(todos) == 0:
        if is_str_fit_terminal(EMPTY_LIST_STR, console):
            return EMPTY_LIST_STR

        return SMALL_TERMINAL_STR

    if console.height <= 5 or not is_str_fit_terminal(CONTROLS_STR, console):
        return SMALL_TERMINAL_STR

    window = select_window(todos, current_line, console.height - 5)

    s = "\n".join(window)
    return f"{CONTROLS_STR}\n{s}"


def todo_symbol_maker(todo: Todo) -> str:
    return FILLED_SQUARE if todo.is_done else EMPTY_SQUARE


def select_window(
    todos: Sequence[Todo], current_idx: int, window_length: int
) -> list[str]:
    n = len(todos)

    if n <= window_length:
        return [
            format_todo(todo, i == current_idx) for i, todo in enumerate(todos)
        ]

    offset = window_length // 2
    result = []

    for i in range(-offset, offset + 1):
        idx = (current_idx + i) % n
        result.append(format_todo(todos[idx], i == 0))

    return result


def format_todo(todo: Todo, is_selected: bool) -> str:
    square = todo_symbol_maker(todo)
    text = todo.todo_text

    if is_selected:
        return f"> {square} [bold black on cyan]{text}[/]"

    return f"  {square} {text}"


def is_str_fit_terminal(s: str, console: Console) -> bool:
    if console.height < s.count("\n"):
        return False

    console_size = console.height * console.width

    return len(s) < console_size


def move_cursor(current_line: int, direction: int, length: int) -> int:
    return (current_line + direction) % length
