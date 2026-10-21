import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Ruta del archivo SQLite. Se puede sobreescribir con la variable de entorno
# DB_PATH (por ejemplo, para apuntar a un volumen en Docker: /data/data.db).
DB_PATH = os.getenv("DB_PATH", "data.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from app.pets.pet_model import Pet  # noqa: F401
    from app.students.student_model import Student  # noqa: F401

    Base.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
