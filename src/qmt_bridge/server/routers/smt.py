"""约定式交易（SMT）路由模块 /api/smt/*（需要 API Key 认证）。

对齐 xttrader 真实 SMT API：
- smt_query_quoter — 查询报价方
- smt_query_compact — 查询约定合约
- smt_query_order — 查询 SMT 委托
- smt_negotiate_order_async — 协商下单
- smt_appointment_order_async — 预约委托
- smt_appointment_cancel_async — 取消预约
- smt_compact_renewal_async — 合约展期
- smt_compact_return_async — 合约归还
"""

from fastapi import APIRouter, Depends, Query

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python, ok_response
from ..models import (
    SMTAppointmentCancelRequest,
    SMTAppointmentOrderRequest,
    SMTCompactRenewalRequest,
    SMTCompactReturnRequest,
    SMTNegotiateOrderRequest,
)
from ..security import require_api_key

router = APIRouter(prefix="/api/smt", tags=["smt"], dependencies=[Depends(require_api_key)])


@router.get("/quoter")
def smt_query_quoter(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询报价方信息 → manager.smt_query_quoter()"""
    result = manager.smt_query_quoter(account_id=account_id)
    return ok_response(_numpy_to_python(result))


@router.get("/compact")
def smt_query_compact(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询约定合约列表 → manager.smt_query_compact()"""
    result = manager.smt_query_compact(account_id=account_id)
    return ok_response(_numpy_to_python(result))


@router.get("/orders")
def smt_query_order(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询 SMT 委托 → manager.smt_query_order()"""
    result = manager.smt_query_order(account_id=account_id)
    return ok_response(_numpy_to_python(result))


@router.post("/negotiate_order_async")
def smt_negotiate_order_async(req: SMTNegotiateOrderRequest, manager=Depends(get_trader_manager)):
    """异步协商下单 → manager.smt_negotiate_order_async()"""
    result = manager.smt_negotiate_order_async(
        src_group_id=req.src_group_id,
        order_code=req.order_code,
        date=req.date,
        amount=req.amount,
        apply_rate=req.apply_rate,
        dict_param=req.dict_param,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/appointment_order_async")
def smt_appointment_order_async(req: SMTAppointmentOrderRequest, manager=Depends(get_trader_manager)):
    """异步预约委托 → manager.smt_appointment_order_async()"""
    result = manager.smt_appointment_order_async(
        order_code=req.order_code,
        date=req.date,
        amount=req.amount,
        apply_rate=req.apply_rate,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/appointment_cancel_async")
def smt_appointment_cancel_async(req: SMTAppointmentCancelRequest, manager=Depends(get_trader_manager)):
    """异步取消预约 → manager.smt_appointment_cancel_async()"""
    result = manager.smt_appointment_cancel_async(
        apply_id=req.apply_id,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/compact_renewal_async")
def smt_compact_renewal_async(req: SMTCompactRenewalRequest, manager=Depends(get_trader_manager)):
    """异步合约展期 → manager.smt_compact_renewal_async()"""
    result = manager.smt_compact_renewal_async(
        cash_compact_id=req.cash_compact_id,
        order_code=req.order_code,
        defer_days=req.defer_days,
        defer_num=req.defer_num,
        apply_rate=req.apply_rate,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/compact_return_async")
def smt_compact_return_async(req: SMTCompactReturnRequest, manager=Depends(get_trader_manager)):
    """异步合约归还 → manager.smt_compact_return_async()"""
    result = manager.smt_compact_return_async(
        src_group_id=req.src_group_id,
        cash_compact_id=req.cash_compact_id,
        order_code=req.order_code,
        occur_amount=req.occur_amount,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))
