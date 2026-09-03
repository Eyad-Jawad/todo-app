from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Depends, HTTPException, status, APIRouter
from pydantic import BaseModel

from todo_app.services.utils import Token, rate_limiter
from todo_app.db import queries
from todo_app.db.models import Todo, User

from todo_app.db import get_session



class CreateTodo(BaseModel):
    text: str
    access_token: str


class GeneralTodo(BaseModel):
    todo_id: int
    access_token: str

router = APIRouter()

async def _get_user(session: AsyncSession, access_token: str) -> User:
    user = await queries.get_user_session(session, access_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE, 
            detail="Access token is expired, please log in again to get a new one."
        )

    return user


async def _get_todo(session: AsyncSession, todo_id: int, access_token: str) -> Todo:
    user = await _get_user(session, access_token)

    todo = await queries.get_todo(session, user.id, todo_id)

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="The todo you requested doesn't exist."
        )

    return todo


@router.get("/todos/all", dependencies=[Depends(rate_limiter())],)
async def get_todos(token: Token):
    async with get_session() as session:
        user = await _get_user(session, token.access_token)

        if user.todos == []:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="You don't have any todos."
            )

        return [
            {
                "id":todo.todo_id,
                "todo":todo.todo_text,
                "is_done":todo.is_done,
                "creation_date":todo.creation_date,
            }
            for todo in user.todos
        ]


@router.post("/todos/add", dependencies=[Depends(rate_limiter())],)
async def add_todo(request: CreateTodo):
    async with get_session() as session:
        user = await _get_user(session, request.access_token)

        if len(request.text) > 4096:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE, 
                detail="A todo text can't be longer than 4096 byte."
            )

        if len(user.todos) >= 100:
            raise HTTPException(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                detail="You can't have more than 100 todos."
            )

        await queries.add_todo(session, user.id, request.text)

        return status.HTTP_201_CREATED


@router.patch("/todos/toggle/", dependencies=[Depends(rate_limiter())],)
async def add_todo(request: GeneralTodo):
    async with get_session() as session:
        todo = await _get_todo(session, request.todo_id, request.access_token)

        await queries.toggle_todo(session, todo)

        return status.HTTP_202_ACCEPTED

            
@router.delete("/todos/delete/", dependencies=[Depends(rate_limiter())],)
async def add_todo(request: GeneralTodo):
    async with get_session() as session:
        todo = await _get_todo(session, request.todo_id, request.access_token)

        await queries.delete_todo(session, todo)

        return status.HTTP_202_ACCEPTED


@router.get("/todos/", dependencies=[Depends(rate_limiter())],)
async def get_todo(request: GeneralTodo):
    async with get_session() as session:
        todo = await _get_todo(session, request.todo_id, request.access_token)

        return {
            "id":todo.todo_id,
            "todo":todo.todo_text,
            "is_done":todo.is_done,
            "creation_date":todo.creation_date,
        }
