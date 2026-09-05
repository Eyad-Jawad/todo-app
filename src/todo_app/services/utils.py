import time
import os
from typing import Annotated
from dotenv import load_dotenv

import redis
from fastapi import HTTPException, Request, status
from pydantic import BaseModel, StringConstraints


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


class Token(BaseModel):
    access_token: str

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")

r = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)


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
