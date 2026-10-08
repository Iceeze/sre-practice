from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FromOrm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class AuthorData(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    @field_validator("first_name", "last_name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value


class AuthorOut(AuthorData, FromOrm):
    id: int


class BookData(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    isbn: str = Field(min_length=1, max_length=32)
    publication_year: int | None = Field(default=None, ge=1, le=9999)
    inventory_number: str = Field(min_length=1, max_length=64)
    author_id: int = Field(gt=0)

    @field_validator("title", "isbn", "inventory_number")
    @classmethod
    def trim_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не может быть пустым")
        return value


class BookOut(BookData, FromOrm):
    id: int


class ReaderData(AuthorData):
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$", max_length=16)


class ReaderOut(ReaderData, FromOrm):
    id: int


class LoanData(BaseModel):
    book_id: int = Field(gt=0)
    reader_id: int = Field(gt=0)
    issued_on: date
    due_on: date
    returned_on: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "LoanData":
        if self.due_on < self.issued_on:
            raise ValueError("Срок возврата не может быть раньше даты выдачи")
        if self.returned_on is not None and self.returned_on < self.issued_on:
            raise ValueError("Дата возврата не может быть раньше даты выдачи")
        return self


class LoanOut(LoanData, FromOrm):
    id: int
