from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from todo_app.db import init_db
from todo_app.services import auth, todo
from todo_app.services.utils import r


@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = await init_db()

    yield

    r.close()
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://0.0.0.0:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(todo.router, tags=["todo"])
app.include_router(auth.router, tags=["auth"])
