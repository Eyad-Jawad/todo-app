import time
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel

from todo_app.db import init_db


class Creditential(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str


r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


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


@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = await init_db()

    yield

    r.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
