"""Router — Instrument info endpoints /api/instrument/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from helpers import _numpy_to_python

router = APIRouter(prefix="/api/instrument", tags=["instrument"])


@router.get("/batch_detail")
def get_batch_instrument_detail(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    iscomplete: bool = Query(False, description="是否返回完整信息"),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    raw = xtdata.get_instrument_detail_list(stock_list, iscomplete=iscomplete)
    return {"data": _numpy_to_python(raw)}


@router.get("/type")
def get_instrument_type(
    stock: str = Query(..., description="股票代码，如 600000.SH"),
):
    raw = xtdata.get_instrument_type(stock)
    return {"stock": stock, "type": raw}


@router.get("/ipo_info")
def get_ipo_info(
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    raw = xtdata.get_ipo_info(start_time=start_time, end_time=end_time)
    return {"data": _numpy_to_python(raw)}


@router.get("/index_weight")
def get_index_weight(
    index_code: str = Query(..., description="指数代码，如 000300.SH"),
):
    raw = xtdata.get_index_weight(index_code)
    return {"index_code": index_code, "data": _numpy_to_python(raw)}


@router.get("/st_history")
def get_st_history(
    stock: str = Query(..., description="股票代码"),
):
    raw = xtdata.get_his_st_data(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}
