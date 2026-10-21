from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.database import Base
from app.shared.datetimes import utc_now


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    username: Mapped[str] = mapped_column(String, unique=True)
    email: Mapped[str] = mapped_column(String, unique=True)
    age: Mapped[int] = mapped_column(Integer)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updatedAt: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
