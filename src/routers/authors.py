from typing import Annotated

from fastapi import APIRouter, Depends

from src.dependencies import get_author_service
from src.schemas import AuthorData, AuthorOut
from src.services.authors import AuthorService

router = APIRouter(prefix="/api/authors", tags=["authors"])
ServiceDep = Annotated[AuthorService, Depends(get_author_service)]


@router.get("", response_model=list[AuthorOut])
def list_authors(service: ServiceDep):
    return service.list()


@router.post("", response_model=AuthorOut, status_code=201)
def create_author(data: AuthorData, service: ServiceDep):
    return service.create(data)


@router.get("/{item_id}", response_model=AuthorOut)
def get_author(item_id: int, service: ServiceDep):
    return service.get(item_id)


@router.put("/{item_id}", response_model=AuthorOut)
def update_author(item_id: int, data: AuthorData, service: ServiceDep):
    return service.update(item_id, data)


@router.delete("/{item_id}", status_code=204)
def delete_author(item_id: int, service: ServiceDep) -> None:
    service.delete(item_id)
