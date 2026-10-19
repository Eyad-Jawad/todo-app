from typing import TYPE_CHECKING
from datetime import datetime, UTC, timedelta

from todo_app.db import Base
from todo_app.settings import settings
from sqlalchemy import ForeignKey,DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship

if TYPE_CHECKING:
    from todo_app.db.models import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str]

    expiration_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_time_in_days),
    )
    is_valid: Mapped[bool] = mapped_column(default=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(
        "refresh_tokens",
    )
