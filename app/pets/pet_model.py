from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.datetimes import utc_now


class Pet(Base):
    __tablename__ = "pets"
    __table_args__ = (UniqueConstraint("studentId", "name"),)

    id: Mapped[str] = mapped_column(String, primary_key=True)
    studentId: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    species: Mapped[str] = mapped_column(String)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
