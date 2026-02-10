"""Router — Trading calendar endpoints /api/calendar/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from helpers import _numpy_to_python

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/trading_dates")
def get_trading_dates(
    market: str = Query(..., description="市场代码，如 SH/SZ/IF/DF/SF/ZF"),
    start_time: str = Query("", description="开始时间 YYYYMMDD"),
    end_time: str = Query("", description="结束时间 YYYYMMDD"),
    count: int = Query(-1, description="返回条数"),
):
    raw = xtdata.get_trading_dates(
        market, start_time=start_time, end_time=end_time, count=count
    )
    return {"market": market, "dates": _numpy_to_python(raw)}


@router.get("/holidays")
def get_holidays():
    raw = xtdata.get_holidays()
    return {"holidays": _numpy_to_python(raw)}


@router.get("/trading_calendar")
def get_trading_calendar(
    market: str = Query(..., description="市场代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    raw = xtdata.get_trading_calendar(market, start_time=start_time, end_time=end_time)
    return {"market": market, "calendar": _numpy_to_python(raw)}


@router.get("/trading_period")
def get_trading_period(
    stock: str = Query(..., description="合约代码，如 000001.SZ"),
):
    raw = xtdata.get_trading_period(stock)
    return {"stock": stock, "periods": _numpy_to_python(raw)}
