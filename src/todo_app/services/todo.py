from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from todo_app.db import get_session, queries
from todo_app.db.models import Todo, User
from todo_app.services.auth import get_user_dependncy
from todo_app.services.utils import TodoRequest, TodoResponse, rate_limiter

router = APIRouter()
todo_rate_limiter = rate_limiter()  # In case we want to change some stuff


async def _get_todo(
    session: AsyncSession,
    todo_id: int,
    user_id: int,
) -> Todo:
    todo = await queries.get_todo(session, user_id, todo_id)

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The todo you requested doesn't exist.",
        )

    return todo


@router.get(
    "/api/todos/all",
    dependencies=[Depends(todo_rate_limiter)],
    response_model=list[TodoResponse],
    status_code=status.HTTP_200_OK,
)
async def get_todos(
    user: Annotated[User, Depends(get_user_dependncy)],
):
    if user.todos == []:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You don't have any todos.",
        )

    return user.todos


@router.post(
    "/api/todos/add",
    dependencies=[Depends(todo_rate_limiter)],
    response_model=TodoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_todo(
    user: Annotated[User, Depends(get_user_dependncy)],
    session: Annotated[AsyncSession, Depends(get_session)],
    request: TodoRequest,
):
    if len(user.todos) >= 100:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="You can't have more than 100 todos.",
        )

    return await queries.add_todo(session, user.id, request.text)


@router.patch(
    "/api/todos/toggle/{id}",
    dependencies=[Depends(todo_rate_limiter)],
    response_model=TodoResponse,
    status_code=status.HTTP_200_OK,
)
async def toggle_todo(
    user: Annotated[User, Depends(get_user_dependncy)],
    session: Annotated[AsyncSession, Depends(get_session)],
    id: int,
):
    todo = await _get_todo(session, id, user.id)

    await queries.toggle_todo(session, todo)

    return todo


@router.delete(
    "/api/todos/delete{id}",
    dependencies=[Depends(todo_rate_limiter)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_todo(
    user: Annotated[User, Depends(get_user_dependncy)],
    session: Annotated[AsyncSession, Depends(get_session)],
    id: int,
):
    todo = await _get_todo(session, id, user.id)

    await queries.delete_todo(session, todo)


@router.get(
    "/api/todos/{id}",
    dependencies=[Depends(todo_rate_limiter)],
    response_model=TodoResponse,
    status_code=status.HTTP_200_OK,
)
async def get_todo(
    user: Annotated[User, Depends(get_user_dependncy)],
    session: Annotated[AsyncSession, Depends(get_session)],
    id: int,
):
    todo = await _get_todo(session, id, user.id)

    return todo
