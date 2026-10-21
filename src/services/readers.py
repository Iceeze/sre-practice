from src.metrics import READERS_REGISTERED
from src.models import Reader
from src.schemas import ReaderData
from src.services.base import BaseService


class ReaderService(BaseService):
    model = Reader

    def create(self, data: ReaderData) -> Reader:
        reader = super().create(data)
        READERS_REGISTERED.inc()
        return reader
