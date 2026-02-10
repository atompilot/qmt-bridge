"""Router — Trading calendar endpoints /api/calendar/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

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


# ---------------------------------------------------------------------------
# New endpoints (Step 5)
# ---------------------------------------------------------------------------


@router.get("/is_trading_date")
def is_trading_date(
    market: str = Query(..., description="市场代码"),
    date: str = Query(..., description="日期 YYYYMMDD"),
):
    """Check whether a given date is a trading date."""
    raw = xtdata.get_trading_dates(market, start_time=date, end_time=date)
    dates = _numpy_to_python(raw)
    return {"market": market, "date": date, "is_trading": len(dates) > 0}


@router.get("/prev_trading_date")
def get_prev_trading_date(
    market: str = Query(..., description="市场代码"),
    date: str = Query("", description="参考日期 YYYYMMDD，默认今天"),
):
    """Get the previous trading date relative to a given date."""
    raw = xtdata.get_trading_dates(market, end_time=date, count=2)
    dates = _numpy_to_python(raw)
    if len(dates) >= 2:
        return {"market": market, "prev_trading_date": dates[-2]}
    return {"market": market, "prev_trading_date": dates[0] if dates else None}


@router.get("/next_trading_date")
def get_next_trading_date(
    market: str = Query(..., description="市场代码"),
    date: str = Query("", description="参考日期 YYYYMMDD，默认今天"),
):
    """Get the next trading date relative to a given date."""
    raw = xtdata.get_trading_dates(market, start_time=date, count=2)
    dates = _numpy_to_python(raw)
    if len(dates) >= 2:
        return {"market": market, "next_trading_date": dates[1]}
    return {"market": market, "next_trading_date": dates[0] if dates else None}


@router.get("/trading_dates_count")
def get_trading_dates_count(
    market: str = Query(..., description="市场代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """Count number of trading dates in a range."""
    raw = xtdata.get_trading_dates(market, start_time=start_time, end_time=end_time)
    dates = _numpy_to_python(raw)
    return {"market": market, "count": len(dates)}


@router.get("/trading_time")
def get_trading_time(
    stock: str = Query(..., description="合约代码"),
):
    """Get trading time info for a stock (alias for trading_period with richer info)."""
    raw = xtdata.get_trading_period(stock)
    return {"stock": stock, "trading_time": _numpy_to_python(raw)}
