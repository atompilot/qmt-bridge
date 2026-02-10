"""Router — Bank transfer endpoints /api/bank/* (requires API Key)."""

from fastapi import APIRouter, Depends

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python
from ..models import BankTransferRequest
from ..security import require_api_key

router = APIRouter(prefix="/api/bank", tags=["bank"], dependencies=[Depends(require_api_key)])


@router.post("/transfer_in")
def bank_transfer_in(req: BankTransferRequest, manager=Depends(get_trader_manager)):
    """Transfer funds from bank to securities account (银行转证券)."""
    result = manager.bank_transfer(
        direction=0,
        amount=req.amount,
        bank_code=req.bank_code,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/transfer_out")
def bank_transfer_out(req: BankTransferRequest, manager=Depends(get_trader_manager)):
    """Transfer funds from securities account to bank (证券转银行)."""
    result = manager.bank_transfer(
        direction=1,
        amount=req.amount,
        bank_code=req.bank_code,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.get("/balance")
def query_bank_balance(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query bank account balance."""
    result = manager.query_bank_balance(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/transfer_records")
def query_bank_transfer_records(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query bank transfer records."""
    result = manager.query_bank_transfer_records(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/banks")
def query_bound_banks(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query bound bank accounts."""
    result = manager.query_bound_banks(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/transfer_limit")
def query_transfer_limit(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query bank transfer limit."""
    result = manager.query_transfer_limit(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/available_amount")
def query_bank_available(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query available amount for bank transfer."""
    result = manager.query_bank_available(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/status")
def query_bank_transfer_status(
    transfer_id: str = "",
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query status of a specific bank transfer."""
    result = manager.query_bank_transfer_status(transfer_id=transfer_id, account_id=account_id)
    return {"data": _numpy_to_python(result)}
