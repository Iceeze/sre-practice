from typing import Annotated

from fastapi import APIRouter, Depends

from src.dependencies import get_reader_service
from src.schemas import ReaderData, ReaderOut
from src.services.readers import ReaderService

router = APIRouter(prefix="/api/readers", tags=["readers"])
ServiceDep = Annotated[ReaderService, Depends(get_reader_service)]


@router.get("", response_model=list[ReaderOut])
def list_readers(service: ServiceDep):
    return service.list()


@router.post("", response_model=ReaderOut, status_code=201)
def create_reader(data: ReaderData, service: ServiceDep):
    return service.create(data)


@router.get("/{item_id}", response_model=ReaderOut)
def get_reader(item_id: int, service: ServiceDep):
    return service.get(item_id)


@router.put("/{item_id}", response_model=ReaderOut)
def update_reader(item_id: int, data: ReaderData, service: ServiceDep):
    return service.update(item_id, data)


@router.delete("/{item_id}", status_code=204)
def delete_reader(item_id: int, service: ServiceDep) -> None:
    service.delete(item_id)
