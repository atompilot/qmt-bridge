"""Router — ETF & convertible bond endpoints /api/etf/* and /api/cb/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from helpers import _numpy_to_python

etf_router = APIRouter(prefix="/api/etf", tags=["etf"])
cb_router = APIRouter(prefix="/api/cb", tags=["cb"])


@etf_router.get("/list")
def get_etf_list():
    stock_list = xtdata.get_stock_list_in_sector("沪深ETF")
    return {"count": len(stock_list), "stocks": stock_list}


@etf_router.get("/info")
def get_etf_info():
    raw = xtdata.get_etf_info()
    return {"data": _numpy_to_python(raw)}


@cb_router.get("/info")
def get_cb_info(
    stock: str = Query(..., description="可转债代码"),
):
    raw = xtdata.get_cb_info(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}
