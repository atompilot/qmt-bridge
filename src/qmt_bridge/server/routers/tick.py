"""L2/Tick 逐笔数据路由模块 /api/tick/*。

提供 Level-2 行情的逐笔报价、逐笔委托、逐笔成交数据端点，
以及千档行情（L2 thousand）相关接口。
底层调用 xtquant.xtdata 的 L2 数据接口，包括：
- xtdata.get_l2_quote()            — 获取 L2 逐笔报价
- xtdata.get_l2_order()            — 获取 L2 逐笔委托
- xtdata.get_l2_transaction()      — 获取 L2 逐笔成交
- xtdata.get_l2_thousand_quote()   — 获取 L2 千档行情报价
- xtdata.get_l2_thousand_orderbook() — 获取 L2 千档委托簿
- xtdata.get_l2_thousand_trade()   — 获取 L2 千档成交数据
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/tick", tags=["tick"])


@router.get("/l2_quote")
def get_l2_quote(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    """获取 L2 逐笔报价数据。

    Args:
        stock: 股票代码，如 000001.SZ。
        start_time: 开始时间。
        end_time: 结束时间。
        count: 返回条数，-1 表示不限。

    Returns:
        该股票的 L2 逐笔报价数据。

    底层调用: xtdata.get_l2_quote(field_list=[], stock_code=..., ...)
    """
    raw = xtdata.get_l2_quote(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/l2_order")
def get_l2_order(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    """获取 L2 逐笔委托数据。

    包含每一笔委托挂单的详细信息（价格、数量、方向等）。

    Args:
        stock: 股票代码。
        start_time: 开始时间。
        end_time: 结束时间。
        count: 返回条数，-1 表示不限。

    Returns:
        该股票的 L2 逐笔委托数据。

    底层调用: xtdata.get_l2_order(field_list=[], stock_code=..., ...)
    """
    raw = xtdata.get_l2_order(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/l2_transaction")
def get_l2_transaction(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    """获取 L2 逐笔成交数据。

    包含每一笔撮合成交的详细信息（价格、数量、买卖标志等）。

    Args:
        stock: 股票代码。
        start_time: 开始时间。
        end_time: 结束时间。
        count: 返回条数，-1 表示不限。

    Returns:
        该股票的 L2 逐笔成交数据。

    底层调用: xtdata.get_l2_transaction(field_list=[], stock_code=..., ...)
    """
    raw = xtdata.get_l2_transaction(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


# ---------------------------------------------------------------------------
# L2 千档行情端点
# ---------------------------------------------------------------------------


@router.get("/l2_thousand_quote")
def get_l2_thousand_quote(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    """获取 L2 千档行情报价数据。

    千档行情比普通 L2 行情提供更深层次的挂单价位数据。

    Args:
        stock: 股票代码。
        start_time: 开始时间。
        end_time: 结束时间。
        count: 返回条数，-1 表示不限。

    Returns:
        该股票的 L2 千档行情报价数据。

    底层调用: xtdata.get_l2_thousand_quote(field_list=[], stock_code=..., ...)
    """
    raw = xtdata.get_l2_thousand_quote(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/l2_thousand_orderbook")
def get_l2_thousand_orderbook(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    """获取 L2 千档委托簿数据。

    提供千档级别的委托簿（买卖各千档挂单明细）。

    Args:
        stock: 股票代码。
        start_time: 开始时间。
        end_time: 结束时间。
        count: 返回条数，-1 表示不限。

    Returns:
        该股票的 L2 千档委托簿数据。

    底层调用: xtdata.get_l2_thousand_orderbook(field_list=[], stock_code=..., ...)
    """
    raw = xtdata.get_l2_thousand_orderbook(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/l2_thousand_trade")
def get_l2_thousand_trade(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    """获取 L2 千档成交数据。

    Args:
        stock: 股票代码。
        start_time: 开始时间。
        end_time: 结束时间。
        count: 返回条数，-1 表示不限。

    Returns:
        该股票的 L2 千档成交数据。

    底层调用: xtdata.get_l2_thousand_trade(field_list=[], stock_code=..., ...)
    """
    raw = xtdata.get_l2_thousand_trade(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


# ---------------------------------------------------------------------------
# 新增端点
# ---------------------------------------------------------------------------


@router.get("/l2_thousand_queue")
def get_l2_thousand_queue(
    stock: str = Query(..., description="股票代码"),
):
    """获取 L2 千档队列数据 → xtdata.get_l2thousand_queue()"""
    raw = xtdata.get_l2thousand_queue(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/broker_queue")
def get_broker_queue(
    stock: str = Query(..., description="股票代码"),
):
    """获取经纪商队列数据 → xtdata.get_broker_queue_data()"""
    raw = xtdata.get_broker_queue_data(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/order_rank")
def get_order_rank(
    stock: str = Query(..., description="股票代码"),
):
    """获取委托排名数据 → xtdata.get_order_rank()"""
    raw = xtdata.get_order_rank(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}
