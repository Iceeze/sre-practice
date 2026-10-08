from sqlalchemy import select

from src.models import Book, Loan, Reader
from src.schemas import LoanData
from src.services.base import BaseService


class LoanService(BaseService):
    model = Loan

    def list(self) -> list[Loan]:
        return list(self.db.scalars(select(Loan).order_by(Loan.id.desc())).all())

    def _ensure_links(self, data: LoanData) -> None:
        self._get(Book, data.book_id)
        self._get(Reader, data.reader_id)

    def create(self, data: LoanData) -> Loan:
        self._ensure_links(data)
        return super().create(data)

    def update(self, item_id: int, data: LoanData) -> Loan:
        self.get(item_id)
        self._ensure_links(data)
        return super().update(item_id, data)
