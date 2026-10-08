from datetime import date

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Book"]] = relationship(
        back_populates="author", passive_deletes=True
    )


class Book(Base):
    __tablename__ = "books"
    __table_args__ = (
        CheckConstraint(
            "publication_year BETWEEN 1 AND 9999", name="ck_books_publication_year"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    isbn: Mapped[str] = mapped_column(String(32))
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inventory_number: Mapped[str] = mapped_column(String(64), unique=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("authors.id", ondelete="RESTRICT")
    )
    author: Mapped[Author] = relationship(back_populates="books")
    loans: Mapped[list["Loan"]] = relationship(
        back_populates="book", passive_deletes=True
    )


class Reader(Base):
    __tablename__ = "readers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str] = mapped_column(String(16), unique=True)
    loans: Mapped[list["Loan"]] = relationship(
        back_populates="reader", passive_deletes=True
    )


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        CheckConstraint("due_on >= issued_on", name="ck_loans_due_on"),
        CheckConstraint(
            "returned_on IS NULL OR returned_on >= issued_on",
            name="ck_loans_returned_on",
        ),
        Index(
            "uq_loans_one_active_per_book",
            "book_id",
            unique=True,
            postgresql_where="returned_on IS NULL",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id", ondelete="RESTRICT"))
    reader_id: Mapped[int] = mapped_column(
        ForeignKey("readers.id", ondelete="RESTRICT")
    )
    issued_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    returned_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    book: Mapped[Book] = relationship(back_populates="loans")
    reader: Mapped[Reader] = relationship(back_populates="loans")
