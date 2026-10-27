import time
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
import redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from sqlalchemy.ext.asyncio import AsyncSession

from todo_app.db import get_session
from todo_app.db.models import User
from todo_app.db.queries import (
    get_user,
    is_refresh_token_valid,
)
from todo_app.settings import settings


class Creditential(BaseModel):
    username: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, max_length=16, min_length=3, ascii_only=True
        ),
    ]
    password: Annotated[
        str,
        StringConstraints(strip_whitespace=True, max_length=36, min_length=8),
    ]


class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    todo_id: int
    todo_text: str
    creation_date: datetime
    is_done: bool = Field(default=True)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    todos: list[TodoResponse]


class JsonWebTokenBase(BaseModel):
    token: str
    expiration_date: datetime


class RefreshTokenResponse(JsonWebTokenBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int


class AccessTokenResponse(JsonWebTokenBase):
    pass


class TodoRequest(BaseModel):
    text: str = Field(max_length=4096)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


async def get_user_dependncy(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    try:
        decoded = jwt.decode(
            token,
            settings.secret_str.get_secret_value(),
            algorithms=[settings.algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Expired token."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token."
        )

    user = await get_user(session, int(decoded["sub"]))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token, account was deleted.",
        )
        # Either that, or our production got compromised
        # and the secret key was leaked.

    if decoded.get("ref") and not (
        await is_refresh_token_valid(session, token)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired refresh token.",
        )

    return user


r = redis.Redis.from_url(settings.redis_url)


def rate_limiter(
    limit: int = 30,
    window: int = 60,  # seconds
):
    async def dependency(
        user: Annotated[User, Depends(get_user_dependncy)],
    ):
        now = int(time.time())
        window_start = now - (now % window)

        key = f"rl:{user.id}:{window_start}"
        current = r.incr(key)

        if current == 1:
            r.expire(key, window)

        elif current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded, please try again later.",
            )

    return dependency


def ip_rate_limiter(
    limit: int = 10,
    window: int = 5 * 60,  # seconds
):
    async def dependency(request: Request):
        identifier = request.client.host if request.client else None

        if identifier is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to identify sender.",
            )

        now = int(time.time())
        window_start = now - (now % window)

        key = f"rl:{identifier}:{window_start}"
        current = r.incr(key)

        if current == 1:
            r.expire(key, window)

        elif current > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded, please try again later.",
            )

    return dependency


def create_json_web_token(
    data: dict, is_access_token: bool, time_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()

    if time_delta:
        expiration_date = datetime.now(UTC) + time_delta
    elif is_access_token:
        expiration_date = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_time_in_minutes
        )
    else:
        expiration_date = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_time_in_days
        )
        to_encode.update({"ref": True})

    to_encode.update({"exp": expiration_date})

    return jwt.encode(
        to_encode,
        settings.secret_str.get_secret_value(),
        algorithm=settings.algorithm,
    )
