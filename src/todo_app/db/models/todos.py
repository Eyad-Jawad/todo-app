from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from .. import Base

class Todo(Base):
    __tablename__ = "todos"

    todo_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column()
    todo_text: Mapped[str] = mapped_column()
    creation_date: Mapped[datetime] = mapped_column()
    is_done: Mapped[bool] = mapped_column()
