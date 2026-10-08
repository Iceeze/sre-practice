from src.models import Author
from src.services.base import BaseService


class AuthorService(BaseService):
    model = Author
