from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.authors import AuthorService
from src.services.base import DatabaseUnavailableError
from src.services.books import BookService
from src.services.loans import LoanService
from src.services.readers import ReaderService

SessionDep = Annotated[Session, Depends(get_db)]


def check_database(db: SessionDep) -> None:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise DatabaseUnavailableError("База данных недоступна") from None


def get_author_service(db: SessionDep) -> AuthorService:
    return AuthorService(db)


def get_book_service(db: SessionDep) -> BookService:
    return BookService(db)


def get_reader_service(db: SessionDep) -> ReaderService:
    return ReaderService(db)


def get_loan_service(db: SessionDep) -> LoanService:
    return LoanService(db)
