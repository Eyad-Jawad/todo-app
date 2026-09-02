from contextlib import asynccontextmanager
from fastapi import FastAPI
from todo_app.db import init_db
from pydantic import BaseModel

class Creditential(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str

@asynccontextmanager
async def lifespan(_app: FastAPI):
    engine = await init_db()

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)
