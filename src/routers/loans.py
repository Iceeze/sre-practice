from typing import Annotated

from fastapi import APIRouter, Depends

from src.dependencies import get_loan_service
from src.schemas import LoanData, LoanOut
from src.services.loans import LoanService

router = APIRouter(prefix="/api/loans", tags=["loans"])
ServiceDep = Annotated[LoanService, Depends(get_loan_service)]


@router.get("", response_model=list[LoanOut])
def list_loans(service: ServiceDep):
    return service.list()


@router.post("", response_model=LoanOut, status_code=201)
def create_loan(data: LoanData, service: ServiceDep):
    return service.create(data)


@router.get("/{item_id}", response_model=LoanOut)
def get_loan(item_id: int, service: ServiceDep):
    return service.get(item_id)


@router.put("/{item_id}", response_model=LoanOut)
def update_loan(item_id: int, data: LoanData, service: ServiceDep):
    return service.update(item_id, data)


@router.delete("/{item_id}", status_code=204)
def delete_loan(item_id: int, service: ServiceDep) -> None:
    service.delete(item_id)
