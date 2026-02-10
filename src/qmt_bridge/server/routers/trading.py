"""Router — Trading endpoints /api/trading/* (requires API Key)."""

from fastapi import APIRouter, Depends

from ..deps import get_trader_manager
from ..helpers import _numpy_to_python
from ..models import (
    AsyncCancelRequest,
    AsyncOrderRequest,
    CancelRequest,
    ExportDataRequest,
    OrderRequest,
    QueryAssetRequest,
    QueryOrderRequest,
    QueryPositionRequest,
    SyncTransactionRequest,
)
from ..security import require_api_key

router = APIRouter(prefix="/api/trading", tags=["trading"], dependencies=[Depends(require_api_key)])


@router.post("/order")
def place_order(req: OrderRequest, manager=Depends(get_trader_manager)):
    """Place a new order."""
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
    """Cancel an existing order."""
    result = manager.cancel_order(
        order_id=req.order_id,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.get("/orders")
def query_orders(
    account_id: str = "",
    cancelable_only: bool = False,
    manager=Depends(get_trader_manager),
):
    """Query current orders."""
    result = manager.query_orders(account_id=account_id, cancelable_only=cancelable_only)
    return {"data": _numpy_to_python(result)}


@router.get("/positions")
def query_positions(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query current positions."""
    result = manager.query_positions(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/asset")
def query_asset(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query account asset information."""
    result = manager.query_asset(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/trades")
def query_trades(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query trade records."""
    result = manager.query_trades(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/order_detail")
def query_order_detail(
    order_id: int = 0,
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query details for a specific order."""
    result = manager.query_order_detail(order_id=order_id, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.post("/batch_order")
def batch_order(orders: list[OrderRequest], manager=Depends(get_trader_manager)):
    """Place multiple orders at once."""
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
    """Cancel multiple orders at once."""
    results = []
    for req in cancel_requests:
        result = manager.cancel_order(order_id=req.order_id, account_id=req.account_id)
        results.append({"order_id": req.order_id, "result": _numpy_to_python(result)})
    return {"data": results}


@router.get("/account_status")
def get_account_status(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Get trading account connection status."""
    result = manager.get_account_status(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/account_info")
def get_account_info(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Get trading account basic information."""
    result = manager.get_account_info(account_id=account_id)
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# Async order/cancel
# ------------------------------------------------------------------


@router.post("/order_async")
def place_order_async(req: AsyncOrderRequest, manager=Depends(get_trader_manager)):
    """Place an order asynchronously (result via WebSocket callback)."""
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
    """Cancel an order asynchronously (result via WebSocket callback)."""
    result = manager.cancel_order_async(
        order_id=req.order_id,
        account_id=req.account_id,
    )
    return {"seq": result, "status": "async_submitted"}


# ------------------------------------------------------------------
# Single-item queries
# ------------------------------------------------------------------


@router.get("/order/{order_id}")
def query_single_order(
    order_id: int,
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query a single order by order_id."""
    result = manager.query_single_order(order_id=order_id, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/trade/{trade_id}")
def query_single_trade(
    trade_id: int,
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query a single trade by trade_id."""
    result = manager.query_single_trade(trade_id=trade_id, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/position/{stock_code}")
def query_single_position(
    stock_code: str,
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query position for a single stock."""
    result = manager.query_single_position(stock_code=stock_code, account_id=account_id)
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# Position statistics
# ------------------------------------------------------------------


@router.get("/position_statistics")
def query_position_statistics(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query position statistics summary."""
    result = manager.query_position_statistics(account_id=account_id)
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# IPO queries
# ------------------------------------------------------------------


@router.get("/new_purchase_limit")
def query_new_purchase_limit(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query IPO new purchase limit."""
    result = manager.query_new_purchase_limit(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/ipo_data")
def query_ipo_data(manager=Depends(get_trader_manager)):
    """Query IPO calendar data."""
    result = manager.query_ipo_data()
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# Account infos (all accounts)
# ------------------------------------------------------------------


@router.get("/account_infos")
def query_account_infos(manager=Depends(get_trader_manager)):
    """Query info for all registered trading accounts."""
    result = manager.query_account_infos()
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# COM queries (期权/期货)
# ------------------------------------------------------------------


@router.get("/com_fund")
def query_com_fund(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query COM fund (option/future account funds)."""
    result = manager.query_com_fund(account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.get("/com_position")
def query_com_position(
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query COM positions (option/future account positions)."""
    result = manager.query_com_position(account_id=account_id)
    return {"data": _numpy_to_python(result)}


# ------------------------------------------------------------------
# Data export / external sync
# ------------------------------------------------------------------


@router.post("/export_data")
def export_data(req: ExportDataRequest, manager=Depends(get_trader_manager)):
    """Export trading data to file."""
    result = manager.export_data(
        data_type=req.data_type,
        file_path=req.file_path,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}


@router.get("/query_data")
def query_data(
    data_type: str = "orders",
    account_id: str = "",
    manager=Depends(get_trader_manager),
):
    """Query exported trading data."""
    result = manager.query_data(data_type=data_type, account_id=account_id)
    return {"data": _numpy_to_python(result)}


@router.post("/sync_transaction")
def sync_transaction(req: SyncTransactionRequest, manager=Depends(get_trader_manager)):
    """Sync external transaction records into the system."""
    result = manager.sync_transaction_from_external(
        data=req.data,
        account_id=req.account_id,
    )
    return {"status": "ok", "data": _numpy_to_python(result)}
