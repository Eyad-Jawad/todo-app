from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from todo_app.db import Base


class Todo(Base):
    __tablename__ = "todos"

    todo_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    todo_text: Mapped[str] = mapped_column()
    creation_date: Mapped[datetime] = mapped_column()
    is_done: Mapped[bool] = mapped_column()
