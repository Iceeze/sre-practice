from sqlalchemy import select

from src.metrics import LOANS_CREATED, LOANS_RETURNED
from src.models import Book, Loan, Reader
from src.schemas import LoanData
from src.services.base import BaseService, NotFoundError
from src.slo_demo import business_operation


class LoanService(BaseService):
    model = Loan

    def list(self) -> list[Loan]:
        return list(self.db.scalars(select(Loan).order_by(Loan.id.desc())).all())

    def _ensure_links(self, data: LoanData) -> None:
        self._get(Book, data.book_id)
        self._get(Reader, data.reader_id)

    @business_operation("loans")
    def create(self, data: LoanData) -> Loan:
        self._ensure_links(data)
        loan = super().create(data)
        LOANS_CREATED.inc()
        return loan

    def update(self, item_id: int, data: LoanData) -> Loan:
        loan = self.db.scalar(select(Loan).where(Loan.id == item_id).with_for_update())
        if loan is None:
            raise NotFoundError("Запись не найдена")

        was_active = loan.returned_on is None
        self._ensure_links(data)
        loan = super().update(item_id, data)

        if was_active and loan.returned_on is not None:
            LOANS_RETURNED.inc()

        return loan
