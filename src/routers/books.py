from typing import Annotated

from fastapi import APIRouter, Depends

from src.dependencies import get_book_service
from src.schemas import BookData, BookOut
from src.services.books import BookService

router = APIRouter(prefix="/api/books", tags=["books"])
ServiceDep = Annotated[BookService, Depends(get_book_service)]


@router.get("", response_model=list[BookOut])
def list_books(service: ServiceDep):
    return service.list()


@router.post("", response_model=BookOut, status_code=201)
def create_book(data: BookData, service: ServiceDep):
    return service.create(data)


@router.get("/{item_id}", response_model=BookOut)
def get_book(item_id: int, service: ServiceDep):
    return service.get(item_id)


@router.put("/{item_id}", response_model=BookOut)
def update_book(item_id: int, data: BookData, service: ServiceDep):
    return service.update(item_id, data)


@router.delete("/{item_id}", status_code=204)
def delete_book(item_id: int, service: ServiceDep) -> None:
    service.delete(item_id)
