"""ETF 路由模块 /api/etf/*。

提供 ETF 基金的列表查询和成分股信息端点。
底层调用 xtquant 的相关接口：
- xtdata.get_stock_list_in_sector("沪深ETF")  — 获取沪深 ETF 列表
- xtdata.get_client().get_etf_info(code)       — 获取单只 ETF 成分股信息
"""

from fastapi import APIRouter, Query
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
def get_etf_info(
    stock: str = Query(..., description="ETF 代码，如 510300.SH"),
):
    """获取单只 ETF 的申赎信息及成分股列表。

    Args:
        stock: ETF 代码，如 ``510300.SH``。

    Returns:
        stock: ETF 代码。
        name: ETF 名称。
        nav: 单位净值。
        component_count: 成分股数量。
        components: 成分股列表，每项包含 stock_code 和 volume。
        raw: 原始信息（不含成分股明细）。

    底层调用: xtdata.get_client().get_etf_info(stock)
    """
    client = xtdata.get_client()
    raw = client.get_etf_info(stock)
    if not raw:
        return {"stock": stock, "error": "未找到该 ETF 信息"}

    # 提取成分股列表
    stocks_raw = raw.pop("stocks", {})
    components = []
    for code, info in stocks_raw.items():
        components.append({
            "stock_code": code,
            "volume": info.get("componentVolume", 0),
        })

    return {
        "stock": stock,
        "name": raw.get("name", ""),
        "nav": raw.get("nav", 0),
        "component_count": len(components),
        "components": components,
        "raw": _numpy_to_python(raw),
    }
