from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from httpx2 import ASGITransport, AsyncClient

from todo_app.db import context_session
from todo_app.services import app
from todo_app.services.auth import (
    get_user_dependncy,
    ph,
    verify_password,
)
from todo_app.services.utils import create_json_web_token


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def make_account(client):
    response = client.post(
        "/api/auth/sign_up",
        json={
            "username": "TestUser",
            "password": "password123",
        },
    )

    assert response.json() is None
    assert response.status_code == status.HTTP_201_CREATED

    return client


@pytest.fixture
def logged_in_account(make_account):
    client = make_account

    response = client.post(
        "/api/auth/log_in",
        json={"username": "TestUser", "password": "password123"},
    )

    assert response.json()["user_id"] == 1
    assert response.status_code == status.HTTP_200_OK

    return client, response.json()["token"]


def test_verify_password_with_correct():
    hash = ph.hash("password123")
    assert verify_password("password123", hash) == True


def test_verify_password_with_incorrect():
    hash = ph.hash("password123")
    assert verify_password("password321", hash) == False


def test_sign_up_with_unused_username(make_account):
    pass


def test_sign_up_with_used_username(
    make_account,
):
    client = make_account

    response = client.post(
        "/api/auth/sign_up",
        json={
            "username": "TestUser",
            "password": "password123",
        },
    )

    assert response.json() is not None
    assert response.status_code == status.HTTP_409_CONFLICT


@patch("jwt.encode")
def test_login_with_valid_attempt(
    mock_encode,
    make_account,
):
    client = make_account

    mock_encode.return_value = "Token"

    response = client.post(
        "/api/auth/log_in",
        json={"username": "TestUser", "password": "password123"},
    )

    josn_response = response.json()
    assert josn_response["token"] == "Token"
    assert josn_response["user_id"] == 1
    assert josn_response["expiration_date"] is not None
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    ("username, password"),
    [
        ["TestUser", "321drowssap"],
        ["TestUser2", "password123"],
    ],
)
def test_login_with_incorrect_creds(username, password, make_account):
    client = make_account

    response = client.post(
        "/api/auth/log_in",
        json={"username": username, "password": password},
    )

    assert response.json() is not None
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_log_out_with_invalid_token(logged_in_account):
    client, _token = logged_in_account

    response = client.delete(
        "/api/auth/log_out",
        headers={"Authorization": "Bearer lolWrongToken"},
    )

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert response.json() == {"detail": "Method Not Allowed"}


def test_log_out_with_valid_token(logged_in_account):
    client, token = logged_in_account

    response = client.post(
        "/api/auth/log_out",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.parametrize(
    ("username, password"),
    [
        ["TestUser", "321drowssap"],
        ["TestUser2", "password123"],
    ],
)
def test_delete_user_with_invalid_creds(username, password, make_account):
    client = make_account
    response = client.request(
        "DELETE",
        "/api/auth/delete_account",
        json={"username": username, "password": password},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() is not None


def test_delete_user_with_valid_attempt(logged_in_account):
    client, _token = logged_in_account

    response = client.request(
        "DELETE",
        "/api/auth/delete_account",
        json={"username": "TestUser", "password": "password123"},
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT, response.json()


@patch("todo_app.services.auth.create_json_web_token")
def test_get_access_token_with_valid_refresh_token(
    mock_create_token, logged_in_account
):
    client, refresh_token = logged_in_account
    mock_create_token.return_value = "123"

    response = client.get(
        "/api/token",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.json()["token"] == "123"
    assert response.json()["expiration_date"] is not None
    assert response.status_code == status.HTTP_200_OK

    mock_create_token.assert_called_once_with(
        data={"sub": 1}, is_access_token=True
    )


# There are no more get_access_token tests cuz the other
# tests would be the responsibility of get_user_dependncy.


@pytest.mark.asyncio
async def test_get_user_dependncy_with_valid_access_token_token(
    logged_in_account,
):
    token = create_json_web_token(data={"sub": "1"}, is_access_token=True)

    async with context_session() as session:
        user = await get_user_dependncy(token, session)

    assert user.id == 1
    assert user.username == "TestUser"


@pytest.mark.asyncio
async def test_get_user_dependncy_with_valid_refresh_token_token(
    logged_in_account,
):
    _client, token = logged_in_account

    async with context_session() as session:
        user = await get_user_dependncy(token, session)

    assert user.id == 1
    assert user.username == "TestUser"


@pytest.mark.asyncio
async def test_get_user_dependncy_with_invalid_token():
    with pytest.raises(HTTPException):
        async with context_session() as session:
            await get_user_dependncy("123", session)


@pytest.mark.asyncio
async def test_get_user_dependncy_with_expired_token(logged_in_account):
    token = create_json_web_token(
        data={"sub": "1"},
        is_access_token=True,
        time_delta=timedelta(seconds=-100),
    )

    async with context_session() as session:
        with pytest.raises(HTTPException):
            await get_user_dependncy(token, session)


@pytest.mark.asyncio
async def test_get_user_dependncy_with_deleted_account():
    token = create_json_web_token(data={"sub": "1"}, is_access_token=True)

    with pytest.raises(HTTPException):
        async with context_session() as session:
            await get_user_dependncy(token, session)


@pytest.mark.asyncio
async def test_get_user_dependncy_with_invalid_refresh_token(logged_in_account):
    _client, token = logged_in_account

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        assert (
            await ac.post(
                "/api/auth/log_out",
                headers={"Authorization": f"Bearer {token}"},
            )
        ).status_code == status.HTTP_204_NO_CONTENT

    with pytest.raises(HTTPException):
        async with context_session() as session:
            await get_user_dependncy(token, session)
