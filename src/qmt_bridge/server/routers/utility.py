"""Router — Utility endpoints /api/utility/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/utility", tags=["utility"])


@router.get("/stock_name")
def get_stock_name(
    stock: str = Query(..., description="股票代码"),
):
    """Get the Chinese name for a stock code."""
    detail = xtdata.get_instrument_detail(stock)
    name = detail.get("InstrumentName", "") if isinstance(detail, dict) else ""
    return {"stock": stock, "name": name}


@router.get("/batch_stock_name")
def get_batch_stock_name(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
):
    """Get Chinese names for multiple stock codes."""
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_instrument_detail_list(stock_list, iscomplete=False)
    result = {}
    data = _numpy_to_python(raw)
    if isinstance(data, dict):
        for code, info in data.items():
            result[code] = info.get("InstrumentName", "") if isinstance(info, dict) else ""
    return {"data": result}


@router.get("/code_to_market")
def code_to_market(
    stock: str = Query(..., description="股票代码"),
):
    """Determine which market a stock code belongs to."""
    instrument_type = xtdata.get_instrument_type(stock)
    market = stock.split(".")[-1] if "." in stock else ""
    return {"stock": stock, "market": market, "type": instrument_type}


@router.get("/search")
def search_stocks(
    keyword: str = Query(..., description="搜索关键字（代码或名称）"),
    category: str = Query("沪深A股", description="搜索范围"),
    limit: int = Query(20, description="返回条数上限"),
):
    """Search stocks by keyword (code prefix or name)."""
    all_stocks = xtdata.get_stock_list_in_sector(category)
    keyword_upper = keyword.upper()
    matches = [s for s in all_stocks if keyword_upper in s.upper()]
    return {"keyword": keyword, "count": len(matches[:limit]), "stocks": matches[:limit]}
