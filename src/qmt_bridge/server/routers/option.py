"""Router — Option data endpoints /api/option/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/option", tags=["option"])


@router.get("/detail")
def get_option_detail(
    option_code: str = Query(..., description="期权合约代码"),
):
    raw = xtdata.get_option_detail_data(option_code)
    return {"option_code": option_code, "data": _numpy_to_python(raw)}


@router.get("/chain")
def get_option_chain(
    undl_code: str = Query(..., description="标的代码，如 000300.SH"),
):
    raw = xtdata.get_option_undl_data(undl_code)
    return {"undl_code": undl_code, "data": _numpy_to_python(raw)}


@router.get("/list")
def get_option_list(
    undl_code: str = Query(..., description="标的代码，如 000300.SH"),
    dedate: str = Query(..., description="到期日"),
    opttype: str = Query("", description="期权类型"),
    isavailable: bool = Query(False, description="是否仅返回可交易合约"),
):
    raw = xtdata.get_option_list(undl_code, dedate, opttype=opttype, isavailavle=isavailable)
    return {"data": _numpy_to_python(raw)}


@router.get("/history_list")
def get_history_option_list(
    undl_code: str = Query(..., description="标的代码，如 000300.SH"),
    dedate: str = Query(..., description="历史日期"),
):
    raw = xtdata.get_his_option_list(undl_code, dedate)
    return {"data": _numpy_to_python(raw)}
