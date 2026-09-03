from contextlib import asynccontextmanager

from fastapi import FastAPI

from todo_app.db import init_db
from todo_app.services import todo, auth
from todo_app.services.utils import r


@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = await init_db()

    yield

    r.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(todo.router, tags=["todo"])
app.include_router(auth.router, tags=["auth"])
