"""Router — SMT (约定式交易) endpoints /api/smt/* (requires API Key)."""

from fastapi import APIRouter, Depends

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python
from ..models import SMTNegotiateOrderRequest, SMTOrderRequest, SMTQueryRequest
from ..security import require_api_key

router = APIRouter(prefix="/api/smt", tags=["smt"], dependencies=[Depends(require_api_key)])


@router.post("/order")
def smt_order(req: SMTOrderRequest, manager=Depends(get_trader_manager)):
    """Place an SMT order."""
    result = manager.smt_order(
        stock_code=req.stock_code,
        order_type=req.order_type,
        order_volume=req.order_volume,
        price_type=req.price_type,
        price=req.price,
        smt_type=req.smt_type,
        strategy_name=req.strategy_name,
        order_remark=req.order_remark,
        account_id=req.account_id,
    )
    return {"order_id": result, "status": "submitted"}


@router.post("/negotiate_order_async")
def smt_negotiate_order_async(req: SMTNegotiateOrderRequest, manager=Depends(get_trader_manager)):
    """Place an SMT negotiate order asynchronously (result via WebSocket callback)."""
    result = manager.smt_negotiate_order_async(
        stock_code=req.stock_code,
        order_type=req.order_type,
        order_volume=req.order_volume,
        price=req.price,
        compact_id=req.compact_id,
        strategy_name=req.strategy_name,
        order_remark=req.order_remark,
        account_id=req.account_id,
    )
    return {"seq": result, "status": "async_submitted"}


@router.post("/cancel")
def cancel_smt_order(order_id: int, account_id: str = "", manager=Depends(get_trader_manager)):
    """Cancel an SMT order."""
    result = manager.cancel_smt_order(order_id=order_id, account_id=account_id)
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.get("/quoter")
def smt_query_quoter(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query SMT quoter information (报价方信息)."""
    result = manager.smt_query_quoter(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/compact")
def smt_query_compact(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query SMT compacts (约定合约)."""
    result = manager.smt_query_compact(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/appointment")
def query_appointment_info(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query SMT appointment info (约定式预约信息)."""
    result = manager.query_appointment_info(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/secu_info")
def query_smt_secu_info(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query SMT security info (约定式证券信息)."""
    result = manager.query_smt_secu_info(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/secu_rate")
def query_smt_secu_rate(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query SMT security rates (约定式证券费率)."""
    result = manager.query_smt_secu_rate(account_id=account_id)
    return {"data": _numpy_to_python(result)}
