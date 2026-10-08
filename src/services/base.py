from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database import Base


class ServiceError(Exception):
    """An expected failure that the API can translate into an HTTP response."""


class NotFoundError(ServiceError):
    pass


class ConflictError(ServiceError):
    pass


class DatabaseUnavailableError(ServiceError):
    pass


class BaseService:
    model: type[Base]

    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Base]:
        return list(self.db.scalars(select(self.model).order_by(self.model.id)).all())

    def get(self, item_id: int) -> Base:
        return self._get(self.model, item_id)

    def _get(self, model: type[Base], item_id: int) -> Base:
        item = self.db.get(model, item_id)
        if item is None:
            raise NotFoundError("Запись не найдена")
        return item

    def create(self, data: BaseModel) -> Base:
        item = self.model(**data.model_dump())
        self.db.add(item)
        self._commit()
        self.db.refresh(item)
        return item

    def update(self, item_id: int, data: BaseModel) -> Base:
        item = self.get(item_id)
        for key, value in data.model_dump().items():
            setattr(item, key, value)
        self._commit()
        self.db.refresh(item)
        return item

    def delete(self, item_id: int) -> None:
        self.db.delete(self.get(item_id))
        self._commit()

    def _commit(self) -> None:
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", "")
            messages = {
                "readers_phone_key": "Читатель с таким номером телефона уже существует",
                "books_inventory_number_key": "Книга с таким инвентарным номером уже существует",
                "uq_loans_one_active_per_book": "Этот экземпляр книги уже выдан",
            }
            if constraint in messages:
                detail = messages[constraint]
            elif getattr(exc.orig, "sqlstate", "") == "23503":
                detail = "Запись используется в связанных данных"
            else:
                detail = "Операция нарушает ограничение базы данных"
            raise ConflictError(detail) from None
