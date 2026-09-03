from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from todo_app.db import Base

if TYPE_CHECKING:
    from todo_app.db.models import User


class Todo(Base):
    __tablename__ = "todos"

    todo_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    todo_text: Mapped[str] = mapped_column()
    creation_date: Mapped[datetime] = mapped_column()
    is_done: Mapped[bool] = mapped_column()

    user: Mapped["User"] = relationship(
        back_populates="todos",
    )
