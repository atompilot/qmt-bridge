"""Router — Credit trading endpoints /api/credit/* (requires API Key)."""

from fastapi import APIRouter, Depends

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python
from ..models import CreditOrderRequest, CreditQueryRequest
from ..security import require_api_key

router = APIRouter(prefix="/api/credit", tags=["credit"], dependencies=[Depends(require_api_key)])


@router.post("/order")
def credit_order(req: CreditOrderRequest, manager=Depends(get_trader_manager)):
    """Place a credit (margin) trading order."""
    result = manager.credit_order(
        stock_code=req.stock_code,
        order_type=req.order_type,
        order_volume=req.order_volume,
        price_type=req.price_type,
        price=req.price,
        credit_type=req.credit_type,
        strategy_name=req.strategy_name,
        order_remark=req.order_remark,
        account_id=req.account_id,
    )
    return {"order_id": result, "status": "submitted"}


@router.get("/positions")
def query_credit_positions(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query credit trading positions."""
    result = manager.query_credit_positions(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/asset")
def query_credit_asset(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query credit trading account asset."""
    result = manager.query_credit_asset(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/debt")
def query_credit_debt(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query credit debt information."""
    result = manager.query_credit_debt(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/available_amount")
def query_credit_available(
    stock_code: str = "",
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query available credit amount for a stock."""
    result = manager.query_credit_available(stock_code=stock_code, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/slo_stocks")
def query_slo_stocks(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query stocks available for short selling (融券标的)."""
    result = manager.query_slo_stocks(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/fin_stocks")
def query_fin_stocks(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query stocks available for margin buying (融资标的)."""
    result = manager.query_fin_stocks(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/subjects")
def query_credit_subjects(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query credit subject list (标的证券)."""
    result = manager.query_credit_subjects(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/assure")
def query_credit_assure(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query credit assurance / collateral info (担保品)."""
    result = manager.query_credit_assure(account_id=account_id)
    return {"data": _numpy_to_python(result)}
