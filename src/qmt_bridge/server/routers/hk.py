"""港股通路由模块 /api/hk/*。

提供港股通（沪港通、深港通）相关股票列表查询端点。
底层调用 xtquant.xtdata 的板块查询接口获取港股通标的列表：
- xtdata.get_stock_list_in_sector("沪港通")  — 获取沪港通标的
- xtdata.get_stock_list_in_sector("深港通")  — 获取深港通标的
- xtdata.get_stock_list_in_sector("港股通")  — 获取港股通标的（南向）
- xtdata.get_stock_list_in_sector("沪股通")  — 获取沪股通标的（北向）
- xtdata.get_stock_list_in_sector("深股通")  — 获取深股通标的（北向）
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/hk", tags=["hk"])


@router.get("/stock_list")
def get_hk_stock_list():
    """获取全部港股通标的列表（沪港通 + 深港通）。

    Returns:
        count: 标的总数量。
        stocks: 港股通标的代码列表。

    底层调用: xtdata.get_stock_list_in_sector("沪港通") + xtdata.get_stock_list_in_sector("深港通")
    """
    # 合并沪港通和深港通标的列表
    stock_list = xtdata.get_stock_list_in_sector("沪港通") + xtdata.get_stock_list_in_sector("深港通")
    return {"count": len(stock_list), "stocks": stock_list}


@router.get("/connect_stocks")
def get_hk_connect_stocks(
    connect_type: str = Query("north", description="通道类型: north(北向)/south(南向)"),
):
    """按通道方向获取互联互通标的列表。

    Args:
        connect_type: 通道类型。
            - "north"（北向）：境外投资者买入 A 股的标的（沪股通 + 深股通）。
            - "south"（南向）：境内投资者买入港股的标的（港股通）。

    Returns:
        connect_type: 查询的通道类型。
        count: 标的数量。
        stocks: 标的代码列表。

    底层调用: xtdata.get_stock_list_in_sector(...)
    """
    if connect_type == "south":
        # 南向：境内投资者可买卖的港股标的
        stock_list = xtdata.get_stock_list_in_sector("港股通")
    else:
        # 北向：境外投资者可买卖的 A 股标的（沪股通 + 深股通）
        stock_list = xtdata.get_stock_list_in_sector("沪股通") + xtdata.get_stock_list_in_sector("深股通")
    return {"connect_type": connect_type, "count": len(stock_list), "stocks": stock_list}


@router.get("/broker_dict")
def get_hk_broker_dict():
    """获取港股经纪商字典 → xtdata.get_hk_broker_dict()"""
    raw = xtdata.get_hk_broker_dict()
    return {"data": _numpy_to_python(raw)}
