"""Router — ETF & convertible bond endpoints /api/etf/* and /api/cb/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

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


# ---------------------------------------------------------------------------
# New convertible bond endpoints (Step 5)
# ---------------------------------------------------------------------------


@cb_router.get("/list")
def get_cb_list():
    """Get all convertible bond codes."""
    stock_list = xtdata.get_stock_list_in_sector("沪深转债")
    return {"count": len(stock_list), "stocks": stock_list}


@cb_router.get("/detail")
def get_cb_detail(
    stock: str = Query(..., description="可转债代码"),
):
    """Get detailed convertible bond information."""
    raw = xtdata.get_cb_info(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}


@cb_router.get("/conversion_price")
def get_cb_conversion_price(
    stock: str = Query(..., description="可转债代码"),
):
    """Get convertible bond conversion price info."""
    raw = xtdata.get_cb_info(stock)
    data = _numpy_to_python(raw)
    return {"stock": stock, "data": data}


@cb_router.get("/bond_info")
def get_bond_info(
    stock: str = Query(..., description="可转债代码"),
):
    """Get bond-specific information for a convertible bond."""
    raw = xtdata.get_cb_info(stock)
    return {"stock": stock, "data": _numpy_to_python(raw)}
