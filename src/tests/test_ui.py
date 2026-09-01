import pytest
import readchar

from unittest.mock import MagicMock, patch, call, AsyncMock
from todo_app.ui import (
    interface,
    key_event_handler,
    handle_keys,
    format_todos,
    todo_symbol_maker,
    select_window,
    format_todo,
    is_str_fit_terminal,
    move_cursor,
    KeyAction,
)


@pytest.fixture
def mock_console():
    con = MagicMock()
    con.clear = MagicMock()
    con.print = MagicMock()
    con.height = 5
    con.width = 20

    return con


def test_move_cursor_with_in_bound_increment():
    assert move_cursor(0, 1, 2) == 1


def test_move_cursor_with_in_bound_decrement():
    assert move_cursor(1, -1, 2) == 0


def test_move_cursor_with_overflow():
    assert move_cursor(1, 1, 2) == 0


def test_move_cursor_with_underflow():
    assert move_cursor(0, -1, 2) == 1


def test_is_str_fit_with_fit_str(mock_console):
    s = 'a' * 20
    assert is_str_fit_terminal(s, mock_console) == True


def test_is_str_fit_with_height_fit_str(mock_console):
    s = '\n' * 4
    assert is_str_fit_terminal(s, mock_console) == True


def test_is_str_fit_with_size_unfit_str(mock_console):
    s = 'a' * 200
    assert is_str_fit_terminal(s, mock_console) == False


def test_is_str_fit_with_height_unfit_str(mock_console):
    s = '\n' * 6
    assert is_str_fit_terminal(s, mock_console) == False


def test_format_todo_with_selected_todo():
    todo = MagicMock()
    todo.todo_text = "Task"
    todo.is_done = True

    assert format_todo(todo, True) == "> ■ [bold black on cyan]Task[/]"


def test_format_todo_with_not_selected_todo():
    todo = MagicMock()
    todo.todo_text = "Task"
    todo.is_done = True

    assert format_todo(todo, False) == "  ■ Task"

@pytest.mark.parametrize(
    "window_length",
    [10, 5],
)
@patch("todo_app.ui.format_todo")
def test_select_window(mock_format, window_length):
    mock_format.return_value = "a str to make tests simple"
    simple_list = [1, 2, 3, 4, 5]

    assert select_window(simple_list, 3, window_length) == ["a str to make tests simple"] * 5
    assert mock_format.call_count == 5
    assert mock_format.call_args_list == [
        call(1, False),
        call(2, False),
        call(3, False),
        call(4, True),
        call(5, False),
    ]

@pytest.mark.parametrize(
    ("is_done, output"),
    [
        (True, "■"),
        (False, "□"),
    ],
)
def test_symbol_maker(is_done, output):
    todo = MagicMock()
    todo.is_done = is_done
    assert todo_symbol_maker(todo) == output


@patch("todo_app.ui.EMPTY_LIST_STR", "Simple str for tests")
@patch("todo_app.ui.is_str_fit_terminal")
def test_format_todos_with_fit_empty_list(mock_is_fit):
    mock_is_fit.return_value = True

    assert format_todos([], 0, 2) == "Simple str for tests"

    mock_is_fit.assert_called_once_with("Simple str for tests", 2)


@patch("todo_app.ui.SMALL_TERMINAL_STR", "smol")
@patch("todo_app.ui.EMPTY_LIST_STR", "Simple str for tests")
@patch("todo_app.ui.is_str_fit_terminal")
def test_format_todos_with_unfit_empty_list(mock_is_fit):
    mock_is_fit.return_value = False

    assert format_todos([], 0, 2) == "smol"

    mock_is_fit.assert_called_once_with("Simple str for tests", 2)


@patch("todo_app.ui.SMALL_TERMINAL_STR", "smol")
@patch("todo_app.ui.is_str_fit_terminal")
def test_format_todos_with_small_console(mock_is_fit, mock_console):
    assert format_todos([1], 0, mock_console) == "smol"

    mock_is_fit.assert_not_called()


@patch("todo_app.ui.CONTROLS_STR", "str")
@patch("todo_app.ui.SMALL_TERMINAL_STR", "smol")
@patch("todo_app.ui.is_str_fit_terminal")
def test_format_todos_with_unfit_str(mock_is_fit):
    mock_is_fit.return_value = False

    console = MagicMock()
    console.height = 6
    assert format_todos([1], 0, console) == "smol"

    mock_is_fit.assert_called_once_with("str", console)


@patch("todo_app.ui.CONTROLS_STR", "str")
@patch("todo_app.ui.select_window")
@patch("todo_app.ui.is_str_fit_terminal")
def test_format_todos_with_fit_str(mock_is_fit, mock_select):
    mock_is_fit.return_value = True
    mock_select.return_value = ["1", "2"]
    
    console = MagicMock()
    console.height = 6
    assert format_todos([1], 0, console) == "str\n1\n2"

    mock_select.assert_called_once_with([1], 0, 1)
    mock_is_fit.assert_called_once_with("str", console)


@pytest.mark.asyncio
@patch("todo_app.ui.toggle_todo", new_callable=AsyncMock)
@patch("readchar.readkey")
async def test_handle_keys_with_enter(mock_readchar, mock_toggle):
    mock_readchar.return_value = readchar.key.ENTER

    assert await handle_keys([1], 0, 3, 3) == (0, KeyAction.DB_CHANGED)

    mock_toggle.assert_awaited_once_with(3, 1)


@pytest.mark.asyncio
@patch("todo_app.ui.move_cursor")
@patch("readchar.readkey")
async def test_handle_keys_with_down(mock_readchar, mock_move):
    mock_readchar.return_value = readchar.key.DOWN
    mock_move.return_value = 1

    assert await handle_keys([1, 2], 0, 3, 3) == (1, KeyAction.LINE_CHANGED)

    mock_move.assert_called_once_with(0, 1, 2)


@pytest.mark.asyncio
@patch("todo_app.ui.move_cursor")
@patch("readchar.readkey")
async def test_handle_keys_with_up(mock_readchar, mock_move):
    mock_readchar.return_value = readchar.key.UP
    mock_move.return_value = 0

    assert await handle_keys([1, 2], 1, 3, 3) == (0, KeyAction.LINE_CHANGED)

    mock_move.assert_called_once_with(1, -1, 2)


@pytest.mark.asyncio
@patch("todo_app.ui.add_todo", new_callable=AsyncMock)
@patch("readchar.readkey")
@pytest.mark.parametrize(
    "key",
    ["a", "A"],
)
async def test_handle_keys_with_a(mock_readchar, mock_add, key):
    mock_readchar.return_value = key

    assert await handle_keys([1], 0, 3, 2) == (0, KeyAction.DB_CHANGED)

    mock_add.assert_awaited_once_with(2, 3)


@pytest.mark.asyncio
@patch("todo_app.ui.delete_todo", new_callable=AsyncMock)
@patch("readchar.readkey")
@pytest.mark.parametrize(
    "key",
    ["d", "D"],
)
async def test_handle_keys_with_d(mock_readchar, mock_delete, key):
    mock_readchar.return_value = key

    assert await handle_keys([1, 2], 1, 3, 2) == (0, KeyAction.DB_CHANGED)

    mock_delete.assert_awaited_once_with(3, 2)


@pytest.mark.asyncio
@patch("readchar.readkey")
@pytest.mark.parametrize(
    "key",
    ["q", "Q"],
)
async def test_handle_keys_with_q(mock_readchar, key):
    mock_readchar.return_value = key

    assert await handle_keys([1], 1, 3, 2) == (0, KeyAction.QUIT)


@pytest.mark.asyncio 
@patch("readchar.readkey")
@pytest.mark.parametrize(
    "key",
    ["c", "C", "w", "2", readchar.key.BACKSPACE],
)
async def test_handle_keys_for_invalid_key(mock_readchar, key):
    mock_readchar.return_value = key

    assert await handle_keys([1], 1, 3, 2) == (1, KeyAction.NOTHING)


@pytest.mark.asyncio
@patch("todo_app.ui.format_todos")
@patch("todo_app.ui.get_todos", new_callable=AsyncMock)
@patch("todo_app.ui.handle_keys", new_callable=AsyncMock)
async def test_key_event_loop(mock_handle, mock_get, mock_format, mock_console):
    mock_handle.side_effect = [
        (0, KeyAction.DB_CHANGED),
        (1, KeyAction.LINE_CHANGED), 
        (1, KeyAction.NOTHING), 
        (0, KeyAction.QUIT),
    ]

    mock_format.side_effect = [1, 2]

    mock_get.return_value = [1, 2]

    await key_event_handler(3, mock_console, 2, [1], 0)

    mock_get.assert_awaited_once_with(3, 2)

    assert mock_console.clear.call_count == 3

    assert mock_format.call_count == 2
    assert mock_format.call_args_list == [
        call([1, 2], 0, mock_console),
        call([1, 2], 1, mock_console),
    ]

    assert mock_console.print.call_count == 2
    assert mock_console.print.call_args_list == [call(1), call(2)]


class AsyncContextManager:
    async def __aenter__(self, *args, **kwargs):
        pass

    async def __aexit__(self, exc_type, exc, tb):
        pass

@pytest.mark.asyncio
@patch("todo_app.ui.init_db", new_callable=AsyncMock)
@patch("todo_app.ui.get_session")
@patch("todo_app.ui.Console")
@patch("todo_app.ui.get_todos", new_callable=AsyncMock)
@patch("todo_app.ui.format_todos")
@patch("todo_app.ui.key_event_handler", new_callable=AsyncMock)
async def test_interface(mock_event_handler, mock_format, mock_get, mock_console_, mock_session, mock_init, mock_console):
    session = MagicMock()

    instance = AsyncContextManager()
    instance.__aenter__ = AsyncMock(return_value=session)

    mock_session.return_value = instance

    mock_console_.return_value = mock_console

    mock_get.return_value = [1]

    mock_format.return_value = "str"

    await interface(user_id=2)

    mock_init.assert_awaited_once()

    mock_session.assert_called_once()

    mock_console_.assert_called_once()

    mock_get.assert_awaited_once_with(None, 2)

    mock_format.assert_called_once_with([1], 0, mock_console)

    mock_console.print.assert_called_once_with("str")

    mock_event_handler.assert_awaited_once_with(None, mock_console, 2, [1], 0)

