from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from todo_app.db import Base

if TYPE_CHECKING:
    from todo_app.db.models import Todo


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    hash: Mapped[str] = mapped_column()
    access_token: Mapped[str | None] = mapped_column()

    todos: Mapped[list["Todo"]] = relationship(
        back_populates="user",
        cascade="all, delete",
    )
