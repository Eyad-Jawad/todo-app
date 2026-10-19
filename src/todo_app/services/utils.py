import os
import time
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
import redis
from dotenv import load_dotenv
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

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
    is_done = Field(default=True)


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


class TodoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    todo_id: int
    todo_text: str
    creation_date: datetime
    is_done: bool


class TodoRequest(BaseModel):
    text: str = Field(max_length=4096)


load_dotenv()
REDIS_URL = os.environ["REDIS_URL"]

r = redis.Redis.from_url(REDIS_URL)


def rate_limiter(
    limit: int = 30,
    window: int = 60,  # seconds
):
    async def dependency(request: Request):
        api_key = request.headers.get("access_key")
        identifier = api_key or (
            request.client.host if request.client else None
        )
        if identifier is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User has no ip or token.",
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

    to_encode.update({"exp": expiration_date})

    return jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )
