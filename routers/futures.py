"""Router — Futures endpoints /api/futures/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from helpers import _numpy_to_python

router = APIRouter(prefix="/api/futures", tags=["futures"])


@router.get("/main_contract")
def get_main_contract(
    code_market: str = Query(..., description="品种市场代码，如 IF.CFE"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    raw = xtdata.get_main_contract(code_market, start_time=start_time, end_time=end_time)
    return {"code_market": code_market, "data": _numpy_to_python(raw)}


@router.get("/sec_main_contract")
def get_sec_main_contract(
    code_market: str = Query(..., description="品种市场代码，如 IF.CFE"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    raw = xtdata.get_sec_main_contract(code_market, start_time=start_time, end_time=end_time)
    return {"code_market": code_market, "data": _numpy_to_python(raw)}
