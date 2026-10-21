from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from todo_app.db import get_session
from todo_app.db.models import User
from todo_app.db.queries import (
    add_refresh_token,
    add_user,
    delete_user,
    get_user,
    get_user_by_token,
    revoke_token,
)
from todo_app.services.utils import (
    AccessTokenResponse,
    Creditential,
    RefreshTokenResponse,
    create_json_web_token,
    rate_limiter,
)
from todo_app.settings import settings

REQUESTS_LIMIT = 10
REQUESTS_LIMIT_TIME = 60 * 5
router = APIRouter()

ph = PasswordHasher()

oaith2_scheme = OAuth2PasswordBearer(token_url="/api/token")
_refresh_token_oauth2_scheme = OAuth2PasswordBearer(token_url="/api/log_in")


async def get_user_dependncy(
    token: Annotated[str, Depends(_refresh_token_oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    decoded = jwt.decode(token)
    if decoded.get("exp") < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Expired token."
        )

    if not decoded.get("ref"):
        user = await get_user(session, decoded["sub"])

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token, account was deleted.",
            )
        # Either that, or our production got compromised
        # and the secret key was leaked.

        return user

    user = await get_user_by_token(session, token)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired token.",
        )

    return user


@router.post(
    "/auth/sign_up",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
    status_code=status.HTTP_201_CREATED,
)
async def sign_up(
    cred: Creditential,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await get_user(session, cred.username)
    if user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"username {cred.username} is alerady used.",
        )

    hash = await run_in_threadpool(ph.hash, cred.password)

    await add_user(session, cred.username, hash)


@router.post(
    "/auth/log_in",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
    status_code=status.HTTP_200_OK,
    response_model=RefreshTokenResponse,
)
async def log_in(
    cred: Creditential,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await get_user(session, cred.username)
    if user is None or not verify_password(cred.password, user.hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    refresh_token = create_json_web_token(
        data={"sub": user.id, "ref": True}, is_access_token=False
    )
    await add_refresh_token(session, user.id, refresh_token)

    return refresh_token


@router.post(
    "/auth/log_out",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def log_out(
    user: Annotated[User, Depends(get_user_dependncy)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await revoke_token(session, user)


@router.delete(
    "/auth/delete_account",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_account(
    cred: Creditential,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user = await get_user(session, cred.username)
    if user is None or not verify_password(cred.password, user.hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    await delete_user(session, user)


@router.get(
    "/api/token",
    dependencies=[Depends(rate_limiter(REQUESTS_LIMIT, REQUESTS_LIMIT_TIME))],
    status_code=status.HTTP_200_OK,
    response_model=AccessTokenResponse,
)
async def get_access_token(user: Annotated[User, Depends(get_user_dependncy)]):
    return {
        "token": create_json_web_token(
            data={"sub": user.id, "ref": False}, is_access_token=True
        ),
        "expiration_date": datetime.now(UTC)
        + timedelta(minutes=settings.access_token_expire_time_in_minutes),
    }


def verify_password(password: str, hash: str) -> bool:
    try:
        ph.verify(hash, password)
        return True
    except VerifyMismatchError:
        return False
