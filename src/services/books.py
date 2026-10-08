from src.models import Author, Book
from src.schemas import BookData
from src.services.base import BaseService


class BookService(BaseService):
    model = Book

    def create(self, data: BookData) -> Book:
        self._get(Author, data.author_id)
        return super().create(data)

    def update(self, item_id: int, data: BookData) -> Book:
        self.get(item_id)
        self._get(Author, data.author_id)
        return super().update(item_id, data)
