"""ETF 路由模块 /api/etf/*。

提供 ETF 基金的列表查询和基本信息端点。
底层调用 xtquant.xtdata 的相关接口：
- xtdata.get_stock_list_in_sector("沪深ETF")  — 获取沪深 ETF 列表
- xtdata.get_etf_info()                        — 获取 ETF 基本信息
"""

from fastapi import APIRouter
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/etf", tags=["etf"])


@router.get("/list")
def get_etf_list():
    """获取沪深 ETF 列表。

    Returns:
        count: ETF 数量。
        stocks: ETF 代码列表。

    底层调用: xtdata.get_stock_list_in_sector("沪深ETF")
    """
    stock_list = xtdata.get_stock_list_in_sector("沪深ETF")
    return {"count": len(stock_list), "stocks": stock_list}


@router.get("/info")
def get_etf_info():
    """获取全部 ETF 的基本信息。

    返回所有 ETF 的基本信息，包括基金类型、跟踪指数、管理费率等。

    Returns:
        data: ETF 基本信息数据。

    底层调用: xtdata.get_etf_info()
    """
    raw = xtdata.get_etf_info()
    return {"data": _numpy_to_python(raw)}
