"""可转债路由模块 /api/cb/*。

提供可转债的列表查询、详情查询等端点。
底层调用 xtquant.xtdata 的相关接口：
- xtdata.get_stock_list_in_sector("沪深转债")  — 获取沪深可转债列表
- xtdata.get_cb_info()                         — 获取可转债详细信息
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/cb", tags=["cb"])


@router.get("/list")
def get_cb_list():
    """获取沪深可转债代码列表。

    Returns:
        count: 可转债数量。
        stocks: 可转债代码列表。

    底层调用: xtdata.get_stock_list_in_sector("沪深转债")
    """
    stock_list = xtdata.get_stock_list_in_sector("沪深转债")
    return {"count": len(stock_list), "stocks": stock_list}


@router.get("/info")
def get_cb_info(
    stock: str = Query(..., description="可转债代码"),
):
    """获取可转债基本信息。

    Args:
        stock: 可转债代码。

    Returns:
        stock: 可转债代码。
        data: 可转债基本信息（含转股价、到期日等）。

    底层调用: xtdata.get_cb_info(stock)
    """
    raw = xtdata.get_cb_info(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}


