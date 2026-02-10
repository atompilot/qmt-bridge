"""Router — Sector endpoints /api/sector/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from helpers import _numpy_to_python

router = APIRouter(prefix="/api/sector", tags=["sector"])


@router.get("/list")
def get_sector_list():
    sectors = xtdata.get_sector_list()
    return {"sectors": sectors}


@router.get("/stocks")
def get_sector_stocks(
    sector: str = Query(..., description="板块名称，如 沪深A股 / 上证A股 / 深证A股 / 沪深ETF / 上证50 / 沪深300"),
    real_timetag: int = Query(-1, description="历史日期时间戳（毫秒），-1 表示最新"),
):
    stock_list = xtdata.get_stock_list_in_sector(sector, real_timetag=real_timetag)
    return {"sector": sector, "count": len(stock_list), "stocks": stock_list}


@router.get("/info")
def get_sector_info(
    sector: str = Query("", description="板块名称，为空返回所有板块信息"),
):
    raw = xtdata.get_sector_info(sector_name=sector)
    return {"data": _numpy_to_python(raw)}
