"""两融交易路由模块 /api/credit/*（需要 API Key 认证）。

对齐 xttrader 真实信用交易 API：
- credit_order — 信用交易下单（通过 order_type 常量区分）
- query_credit_positions — 查询信用持仓
- query_credit_detail — 查询信用账户资产详情
- query_stk_compacts — 查询信用负债合约
- query_credit_slo_code — 查询融券标的
- query_credit_subjects — 查询标的证券
- query_credit_assure — 查询担保品
"""

from fastapi import APIRouter, Depends, Query

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python, ok_response
from ..models import CreditOrderRequest
from ..security import require_api_key

router = APIRouter(prefix="/api/credit", tags=["credit"], dependencies=[Depends(require_api_key)])


@router.post("/order")
def credit_order(req: CreditOrderRequest, manager=Depends(get_trader_manager)):
    """信用交易下单（通过 order_type 区分融资买入/融券卖出等）。"""
    result = manager.credit_order(
        stock_code=req.stock_code,
        order_type=req.order_type,
        order_volume=req.order_volume,
        price_type=req.price_type,
        price=req.price,
        strategy_name=req.strategy_name,
        order_remark=req.order_remark,
        account_id=req.account_id,
    )
    return {"order_id": result, "status": "submitted"}


@router.get("/positions")
def query_credit_positions(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询两融持仓列表 → manager.query_credit_positions()"""
    result = manager.query_credit_positions(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/asset")
def query_credit_detail(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询信用账户资产详情 → manager.query_credit_detail()"""
    result = manager.query_credit_detail(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/debt")
def query_stk_compacts(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询信用负债合约 → manager.query_stk_compacts()"""
    result = manager.query_stk_compacts(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/slo_stocks")
def query_credit_slo_code(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询融券标的列表 → manager.query_credit_slo_code()"""
    result = manager.query_credit_slo_code(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/subjects")
def query_credit_subjects(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询标的证券列表 → manager.query_credit_subjects()"""
    result = manager.query_credit_subjects(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/assure")
def query_credit_assure(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询担保品信息 → manager.query_credit_assure()"""
    result = manager.query_credit_assure(account_id=account_id)
    return {"data": _numpy_to_python(result)}
