import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL must be set")
    return value


engine = create_engine(database_url(), pool_pre_ping=True, hide_parameters=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
