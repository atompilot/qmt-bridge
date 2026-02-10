"""Router — Tick & L2 data endpoints /api/tick/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from helpers import _numpy_to_python

router = APIRouter(prefix="/api/tick", tags=["tick"])


@router.get("/l2_quote")
def get_l2_quote(
    stock: str = Query(..., description="股票代码，如 000001.SZ"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    raw = xtdata.get_l2_quote(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/l2_order")
def get_l2_order(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    raw = xtdata.get_l2_order(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}


@router.get("/l2_transaction")
def get_l2_transaction(
    stock: str = Query(..., description="股票代码"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    count: int = Query(-1, description="返回条数"),
):
    raw = xtdata.get_l2_transaction(
        field_list=[],
        stock_code=stock,
        start_time=start_time,
        end_time=end_time,
        count=count,
    )
    return {"stock": stock, "data": _numpy_to_python(raw)}
