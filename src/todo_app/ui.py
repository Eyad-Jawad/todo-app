from textwrap import dedent

from rich.console import Console
from sqlalchemy import select
from todo_app.db import init_db, get_session
from todo_app.db.models import Todo

async def interface(user_id: int = 0):
    console = Console()

    await init_db()
    
    async with get_session() as session:
        stmt = select(Todo).where(Todo.user_id == user_id)
        result = await session.execute(stmt)
        todos = result.all()

        console.print(format_todos(todos, console))


def format_todos(todos: list[Todo], console: Console) -> str:
    CONTROLS_STR = dedent("""
        Press:
            [cyan](Enter)[/] to toggle the todo
            [cyan](A)[/]dd to add a new todo
            [cyan](E)[/]dit to edit a highlighted todo
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

    if len(todos) == 0:
        if is_str_fit_terminal(EMPTY_LIST_STR, console):
            return EMPTY_LIST_STR

        return SMALL_TERMINAL_STR

    formatted_str = f"{CONTROLS_STR}\n"

    if not is_str_fit_terminal(formatted_str, console):
        return SMALL_TERMINAL_STR

    for todo in todos:
        is_done = FILLED_SQUARE if todo.is_done else EMPTY_SQUARE

        todo_line = todo.todo_text + is_done

        if is_str_fit_terminal(formatted_str + todo_line, console):
            formatted_str += todo_line + '\n'
        else:
            continue

    return formatted_str


def is_str_fit_terminal(s: str, console: Console) -> bool:
    console_size = console.size.height * console.size.width

    return len(s) < console_size