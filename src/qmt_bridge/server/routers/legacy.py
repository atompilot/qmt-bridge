"""Router — Legacy endpoints from server.py (backward compatibility)."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _market_data_to_records, _numpy_to_python
from ..models import DownloadRequest

router = APIRouter(tags=["legacy"])


@router.get("/api/history")
def get_history(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
    period: str = Query("1d", description="K线周期: tick/1m/5m/15m/30m/60m/1d"),
    count: int = Query(100, description="返回条数"),
    fields: str = Query(
        "open,high,low,close,volume",
        description="字段列表，逗号分隔",
    ),
):
    field_list = [f.strip() for f in fields.split(",")]
    raw = xtdata.get_market_data(
        field_list=field_list,
        stock_list=[stock],
        period=period,
        count=count,
    )
    records = _market_data_to_records(raw, [stock], field_list)
    return {"stock": stock, "period": period, "count": count, "data": records.get(stock, [])}


@router.get("/api/batch_history")
def get_batch_history(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    period: str = Query("1d", description="K线周期"),
    count: int = Query(100, description="返回条数"),
    fields: str = Query(
        "open,high,low,close,volume",
        description="字段列表，逗号分隔",
    ),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    field_list = [f.strip() for f in fields.split(",")]
    raw = xtdata.get_market_data(
        field_list=field_list,
        stock_list=stock_list,
        period=period,
        count=count,
    )
    records = _market_data_to_records(raw, stock_list, field_list)
    return {"stocks": stock_list, "period": period, "count": count, "data": records}


@router.get("/api/full_tick")
def get_full_tick(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_full_tick(code_list=stock_list)
    return {"data": _numpy_to_python(raw)}


@router.get("/api/sector_stocks")
def get_sector_stocks(
    sector: str = Query(..., description="板块名称，如 沪深A股"),
):
    stock_list = xtdata.get_stock_list_in_sector(sector)
    return {"sector": sector, "stocks": stock_list}


@router.get("/api/instrument_detail")
def get_instrument_detail(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
):
    detail = xtdata.get_instrument_detail(stock)
    return {"stock": stock, "detail": _numpy_to_python(detail)}


@router.post("/api/download")
def download_data(req: DownloadRequest):
    xtdata.download_history_data(
        req.stock, period=req.period, start_time=req.start, end_time=req.end
    )
    return {"status": "ok", "stock": req.stock, "period": req.period}
