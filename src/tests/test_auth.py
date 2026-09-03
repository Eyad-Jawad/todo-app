
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from argon2 import PasswordHasher
from fastapi import HTTPException
from todo_app.auth import (
    sign_up,
    login,
    log_out,
    delete_account,
    verify_password,
    ph
)


def test_verify_password_with_correct():
    hash = ph.hash("password123")
    assert verify_password("password123", hash) == True


def test_verify_password_with_incorrect():
    hash = ph.hash("password123")
    assert verify_password("password321", hash) == False


@pytest.mark.asyncio
@patch("todo_app.auth.add_user", new_callable=AsyncMock)
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.get_user", new_callable=AsyncMock)
async def test_sign_up_with_used_username(mock_get, mock_session, mock_add, mock_with_session):
    mock_get.return_value = 1
    mock_session.return_value = mock_with_session

    with pytest.raises(HTTPException):
        await sign_up("user", "123")

    mock_add.assert_not_awaited()


@pytest.mark.asyncio
@patch("todo_app.auth.add_user", new_callable=AsyncMock)
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.get_user", new_callable=AsyncMock)
async def test_sign_up_with_new_user(mock_get, mock_session, mock_add, mock_with_session):
    mock_get.return_value = None
    mock_session.return_value = mock_with_session
    mock_add.return_value = "Token"

    ph = MagicMock()
    ph.hash.return_value = "Hash"
    with patch("todo_app.auth.ph", ph):
        assert await sign_up("user", "123") == {"access_token": "Token"}

    ph.hash.assert_called_once_with("123")

    mock_add.assert_awaited_once_with(None, "user", "Hash")


@pytest.mark.asyncio
@patch("todo_app.auth.set_token", new_callable=AsyncMock)
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.get_user", new_callable=AsyncMock)
async def test_login_with_new_user(mock_get, mock_session, mock_set, mock_with_session):
    mock_get.return_value = None

    mock_session.return_value = mock_with_session

    with pytest.raises(HTTPException):
        await login("user", "123")

    mock_set.assert_not_awaited()


@pytest.mark.asyncio
@patch("todo_app.auth.verify_password")
@patch("todo_app.auth.set_token", new_callable=AsyncMock)
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.get_user", new_callable=AsyncMock)
async def test_login_with_incorrect_password(mock_get, mock_session, mock_set, mock_verify, mock_with_session):
    mock_session.return_value = mock_with_session
    mock_verify.return_value = False

    user = MagicMock()
    user.hash = "Hash"
    mock_get.return_value = user

    with pytest.raises(HTTPException):
        await login("user", "123")

    mock_verify.assert_called_once_with("123", "Hash")

    mock_set.assert_not_awaited()


@pytest.mark.asyncio
@patch("todo_app.auth.verify_password")
@patch("todo_app.auth.set_token", new_callable=AsyncMock)
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.get_user", new_callable=AsyncMock)
async def test_login_with_valid_attempt(mock_get, mock_session, mock_set, mock_verify, mock_with_session):
    mock_session.return_value = mock_with_session
    mock_verify.return_value = True
    mock_set.return_value = "Token"

    user = MagicMock()
    user.hash = "Hash"
    mock_get.return_value = user

    assert await login("user", "123") == {"access_token": "Token"}

    mock_verify.assert_called_once_with("123", "Hash")

    mock_set.assert_awaited_once_with(None, user)


@pytest.mark.asyncio
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.revoke_token")
@patch("todo_app.auth.get_user_session")
async def test_log_out_with_invalid_token(mock_get, mock_revoke, mock_session, mock_with_session):
    mock_get.return_value = None
    mock_session.return_value = mock_with_session

    with pytest.raises(HTTPException):
        await log_out("Hash")

    mock_revoke.assert_not_awaited()


@pytest.mark.asyncio
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.revoke_token")
@patch("todo_app.auth.get_user_session")
async def test_log_out_with_valid_token(mock_get, mock_revoke, mock_session, mock_with_session):
    mock_get.return_value = 1
    mock_session.return_value = mock_with_session

    assert await log_out("Hash") == {"logged_out": True}

    mock_revoke.assert_awaited_once_with(None, 1)


@pytest.mark.asyncio
@patch("todo_app.auth.verify_password")
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.delete_user")
@patch("todo_app.auth.get_user")
async def test_delete_user_with_new_user(mock_get, mock_delete, mock_session, mock_verify, mock_with_session):
    mock_get.return_value = None
    mock_session.return_value = mock_with_session

    with pytest.raises(HTTPException):
        assert await delete_account("user", "123")

    mock_verify.assert_not_called()

    mock_delete.assert_not_awaited()


@pytest.mark.asyncio
@patch("todo_app.auth.verify_password")
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.delete_user")
@patch("todo_app.auth.get_user")
async def test_delete_user_with_incorrect_password(mock_get, mock_delete, mock_session, mock_verify, mock_with_session):
    mock_session.return_value = mock_with_session
    mock_verify.return_value = False

    user = MagicMock()
    user.hash = "Hash"
    mock_get.return_value = user

    with pytest.raises(HTTPException):
        assert await delete_account("user", "123")

    mock_verify.assert_called_once_with("123", "Hash")
    
    mock_delete.assert_not_awaited()


@pytest.mark.asyncio
@patch("todo_app.auth.verify_password")
@patch("todo_app.auth.get_session")
@patch("todo_app.auth.delete_user")
@patch("todo_app.auth.get_user")
async def test_delete_user_with_valid_attempt(mock_get, mock_delete, mock_session, mock_verify, mock_with_session):
    mock_session.return_value = mock_with_session
    mock_verify.return_value = True

    user = MagicMock()
    user.hash = "Hash"
    mock_get.return_value = user

    assert await delete_account("user", "123") == {"account_deleted": True}

    mock_verify.assert_called_once_with("123", "Hash")
    
    mock_delete.assert_awaited_once_with(None, user)

