"""交易操作路由模块 /api/trading/*（需要 API Key 认证）。

对齐 xttrader 真实交易 API，修复参数传递链路。
"""

from fastapi import APIRouter, Depends, Query

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python, ok_response
from ..models import (
    AsyncCancelRequest,
    AsyncOrderRequest,
    CancelBySysidRequest,
    CancelRequest,
    ExportDataRequest,
    OrderRequest,
    QueryDataRequest,
    SyncTransactionRequest,
)
from ..security import require_api_key

router = APIRouter(prefix="/api/trading", tags=["trading"], dependencies=[Depends(require_api_key)])


@router.post("/order")
def place_order(req: OrderRequest, manager=Depends(get_trader_manager)):
    """同步下单 → manager.order()"""
    result = manager.order(
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


@router.post("/cancel")
def cancel_order(req: CancelRequest, manager=Depends(get_trader_manager)):
    """同步撤单 → manager.cancel_order()"""
    result = manager.cancel_order(
        order_id=req.order_id,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.post("/cancel_by_sysid")
def cancel_order_by_sysid(req: CancelBySysidRequest, manager=Depends(get_trader_manager)):
    """按系统编号同步撤单 → manager.cancel_order_stock_sysid()"""
    result = manager.cancel_order_stock_sysid(
        market=req.market,
        sysid=req.sysid,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/cancel_by_sysid_async")
def cancel_order_by_sysid_async(req: CancelBySysidRequest, manager=Depends(get_trader_manager)):
    """按系统编号异步撤单 → manager.cancel_order_stock_sysid_async()"""
    result = manager.cancel_order_stock_sysid_async(
        market=req.market,
        sysid=req.sysid,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.get("/orders")
def query_orders(
    account_id: str = Query("", description="交易账户 ID"),
    cancelable_only: bool = Query(False, description="仅返回可撤委托"),
    manager=Depends(get_trader_manager),
):
    """查询当日委托列表 → manager.query_orders()"""
    result = manager.query_orders(account_id=account_id, cancelable_only=cancelable_only)
    return {"data": _numpy_to_python(result)}


@router.get("/positions")
def query_positions(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询当前持仓列表 → manager.query_positions()"""
    result = manager.query_positions(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/asset")
def query_asset(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询账户资产信息 → manager.query_asset()"""
    result = manager.query_asset(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/trades")
def query_trades(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询当日成交记录 → manager.query_trades()"""
    result = manager.query_trades(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/order_detail")
def query_order_detail(
    order_id: int = Query(0, description="委托编号"),
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询单笔委托详情 → manager.query_order_detail()"""
    result = manager.query_order_detail(order_id=order_id, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.post("/batch_order")
def batch_order(orders: list[OrderRequest], manager=Depends(get_trader_manager)):
    """批量下单。"""
    results = []
    for req in orders:
        result = manager.order(
            stock_code=req.stock_code,
            order_type=req.order_type,
            order_volume=req.order_volume,
            price_type=req.price_type,
            price=req.price,
            strategy_name=req.strategy_name,
            order_remark=req.order_remark,
            account_id=req.account_id,
        )
        results.append({"stock_code": req.stock_code, "order_id": result})
    return {"data": results}


@router.post("/batch_cancel")
def batch_cancel(cancel_requests: list[CancelRequest], manager=Depends(get_trader_manager)):
    """批量撤单。"""
    results = []
    for req in cancel_requests:
        result = manager.cancel_order(order_id=req.order_id, account_id=req.account_id)
        results.append({"order_id": req.order_id, "result": _numpy_to_python(result)})
    return {"data": results}


@router.get("/account_status")
def get_account_status(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """获取交易账户连接状态 → manager.get_account_status()"""
    result = manager.get_account_status(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/account_status_detail")
def query_account_status_detail(manager=Depends(get_trader_manager)):
    """查询账户状态详情 → manager.query_account_status()"""
    result = manager.query_account_status()
    return ok_response(_numpy_to_python(result))


@router.get("/secu_account")
def query_secu_account(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询证券子账户 → manager.query_secu_account()"""
    result = manager.query_secu_account(account_id=account_id)
    return ok_response(_numpy_to_python(result))


# ------------------------------------------------------------------
# 异步委托/撤单
# ------------------------------------------------------------------


@router.post("/order_async")
def place_order_async(req: AsyncOrderRequest, manager=Depends(get_trader_manager)):
    """异步下单 → manager.order_async()"""
    result = manager.order_async(
        stock_code=req.stock_code,
        order_type=req.order_type,
        order_volume=req.order_volume,
        price_type=req.price_type,
        price=req.price,
        strategy_name=req.strategy_name,
        order_remark=req.order_remark,
        account_id=req.account_id,
    )
    return {"seq": result, "status": "async_submitted"}


@router.post("/cancel_async")
def cancel_order_async(req: AsyncCancelRequest, manager=Depends(get_trader_manager)):
    """异步撤单 → manager.cancel_order_async()"""
    result = manager.cancel_order_async(
        order_id=req.order_id,
        account_id=req.account_id,
    )
    return {"seq": result, "status": "async_submitted"}


# ------------------------------------------------------------------
# 单笔查询
# ------------------------------------------------------------------


@router.get("/order/{order_id}")
def query_single_order(
    order_id: int,
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询单笔委托 → manager.query_single_order()"""
    result = manager.query_single_order(order_id=order_id, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/trade/{trade_id}")
def query_single_trade(
    trade_id: int,
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询单笔成交（遍历过滤）→ manager.query_single_trade()"""
    result = manager.query_single_trade(trade_id=trade_id, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/position/{stock_code}")
def query_single_position(
    stock_code: str,
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询单只股票持仓（遍历过滤）→ manager.query_single_position()"""
    result = manager.query_single_position(stock_code=stock_code, account_id=account_id)
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# 新股申购查询
# ------------------------------------------------------------------


@router.get("/new_purchase_limit")
def query_new_purchase_limit(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询新股申购额度 → manager.query_new_purchase_limit()"""
    result = manager.query_new_purchase_limit(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/ipo_data")
def query_ipo_data(manager=Depends(get_trader_manager)):
    """查询 IPO 日历数据 → manager.query_ipo_data()"""
    result = manager.query_ipo_data()
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# 多账户信息
# ------------------------------------------------------------------


@router.get("/account_infos")
def query_account_infos(manager=Depends(get_trader_manager)):
    """查询所有已注册交易账户的信息 → manager.query_account_infos()"""
    result = manager.query_account_infos()
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# COM 查询（期权/期货）
# ------------------------------------------------------------------


@router.get("/com_fund")
def query_com_fund(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询期权/期货账户资金 → manager.query_com_fund()"""
    result = manager.query_com_fund(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/com_position")
def query_com_position(
    account_id: str = Query("", description="交易账户 ID"),
    manager=Depends(get_trader_manager),
):
    """查询期权/期货账户持仓 → manager.query_com_position()"""
    result = manager.query_com_position(account_id=account_id)
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# 数据导出 / 外部同步（对齐 xttrader 真实签名）
# ------------------------------------------------------------------


@router.post("/export_data")
def export_data(req: ExportDataRequest, manager=Depends(get_trader_manager)):
    """导出交易数据 → manager.export_data()"""
    result = manager.export_data(
        result_path=req.result_path,
        data_type=req.data_type,
        start_time=req.start_time,
        end_time=req.end_time,
        user_param=req.user_param,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/query_data")
def query_data(req: QueryDataRequest, manager=Depends(get_trader_manager)):
    """查询已导出的交易数据 → manager.query_data()"""
    result = manager.query_data(
        result_path=req.result_path,
        data_type=req.data_type,
        start_time=req.start_time,
        end_time=req.end_time,
        user_param=req.user_param,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))


@router.post("/sync_transaction")
def sync_transaction(req: SyncTransactionRequest, manager=Depends(get_trader_manager)):
    """同步外部成交记录 → manager.sync_transaction_from_external()"""
    result = manager.sync_transaction_from_external(
        operation=req.operation,
        data_type=req.data_type,
        deal_list=req.deal_list,
        account_id=req.account_id,
    )
    return ok_response(_numpy_to_python(result))
