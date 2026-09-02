from sqlalchemy.orm import Mapped, mapped_column

from todo_app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    hash: Mapped[str] = mapped_column()
    access_token: Mapped[str | None] = mapped_column()
