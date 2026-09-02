from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, status

from todo_app.db import get_session
from todo_app.db.models import User
from todo_app.db.queries import get_user, get_user_session

ph = PasswordHasher()


async def sign_up(username: str, password: str):
    async with get_session() as session:
        user_ = await get_user(username, session)
        if user_ is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"username {username} is alerady used.",
            )

        hash = ph.hash(password)
        access_token = str(uuid4())
        user = User(
            username=username,
            hash=hash,
            access_token=access_token,
        )

        session.add(user)
        await session.commit()

        return {"access_token": access_token}


async def login(username: str, password: str):
    async with get_session() as session:
        user = await get_user(username, session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        if not verify_password(password, user.hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        access_token = str(uuid4())
        user.access_token = access_token
        await session.commit()

        return {"access_token": access_token}


async def log_out(access_token: str):
    async with get_session() as session:
        user = await get_user_session(access_token, session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User doesn't exist.",
            )

        user.access_token = None
        await session.commit()

        return {"logged_out": True}


async def delete_account(username: str, password: str):
    async with get_session() as session:
        user = await get_user(username, session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        if not verify_password(password, user.hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password.",
            )

        await session.delete(user)
        await session.commit()

        return {"account_deleted": True}


def verify_password(password: str, hash: str) -> bool:
    try:
        ph.verify(hash, password)
        return True
    except VerifyMismatchError:
        return False
