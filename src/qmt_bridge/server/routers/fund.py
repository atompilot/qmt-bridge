"""Router — Fund transfer endpoints /api/fund/* (requires API Key)."""

from fastapi import APIRouter, Depends

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python
from ..models import CTPCrossMarketTransferRequest, FundTransferRequest
from ..security import require_api_key

router = APIRouter(prefix="/api/fund", tags=["fund"], dependencies=[Depends(require_api_key)])


@router.post("/transfer")
def fund_transfer(req: FundTransferRequest, manager=Depends(get_trader_manager)):
    """Transfer funds between accounts."""
    result = manager.fund_transfer(
        transfer_direction=req.transfer_direction,
        amount=req.amount,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.get("/transfer_records")
def query_transfer_records(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query fund transfer records."""
    result = manager.query_fund_transfer_records(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/available")
def query_available_fund(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query available fund balance."""
    result = manager.query_available_fund(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.post("/ctp_transfer_in")
def ctp_transfer_in(req: FundTransferRequest, manager=Depends(get_trader_manager)):
    """Transfer funds into CTP account."""
    result = manager.ctp_fund_transfer(
        direction=0,
        amount=req.amount,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/ctp_transfer_out")
def ctp_transfer_out(req: FundTransferRequest, manager=Depends(get_trader_manager)):
    """Transfer funds out of CTP account."""
    result = manager.ctp_fund_transfer(
        direction=1,
        amount=req.amount,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.get("/ctp_balance")
def query_ctp_balance(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query CTP account balance."""
    result = manager.query_ctp_balance(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.post("/ctp_option_to_future")
def ctp_transfer_option_to_future(
    req: CTPCrossMarketTransferRequest,
    manager=Depends(get_trader_manager),
):
    """Transfer from option account to future account (cross-market)."""
    result = manager.ctp_transfer_option_to_future(
        amount=req.amount,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/ctp_future_to_option")
def ctp_transfer_future_to_option(
    req: CTPCrossMarketTransferRequest,
    manager=Depends(get_trader_manager),
):
    """Transfer from future account to option account (cross-market)."""
    result = manager.ctp_transfer_future_to_option(
        amount=req.amount,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}
