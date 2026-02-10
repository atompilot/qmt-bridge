"""Router — System metadata endpoints /api/meta/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/markets")
def get_markets():
    raw = xtdata.get_markets()
    return {"markets": _numpy_to_python(raw)}


@router.get("/periods")
def get_periods():
    raw = xtdata.get_period_list()
    return {"periods": _numpy_to_python(raw)}


@router.get("/stock_list")
def get_stock_list(
    category: str = Query(
        ...,
        description="证券类别，如 沪深A股 / 上证A股 / 深证A股 / 北证A股 / 沪深ETF / 沪深指数",
    ),
):
    stock_list = xtdata.get_stock_list_in_sector(category)
    return {"category": category, "count": len(stock_list), "stocks": stock_list}


@router.get("/last_trade_date")
def get_last_trade_date(
    market: str = Query(..., description="市场代码，如 SH / SZ"),
):
    date = xtdata.get_market_last_trade_date(market)
    return {"market": market, "last_trade_date": date}


# ---------------------------------------------------------------------------
# New status monitoring endpoints (Step 5)
# ---------------------------------------------------------------------------


@router.get("/version")
def get_server_version():
    """Get QMT Bridge server version."""
    from ..._version import __version__

    return {"version": __version__}


@router.get("/xtdata_version")
def get_xtdata_version():
    """Get xtquant/xtdata library version."""
    try:
        import xtquant
        version = getattr(xtquant, "__version__", "unknown")
    except Exception:
        version = "unknown"
    return {"xtdata_version": version}


@router.get("/connection_status")
def get_connection_status():
    """Check xtdata connection status."""
    try:
        status = xtdata.get_client().get_connect_status()
        return {"connected": status}
    except Exception as e:
        return {"connected": False, "error": str(e)}


@router.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}


@router.get("/quote_server_status")
def get_quote_server_status():
    """Get detailed quote server connection status."""
    try:
        status = xtdata.get_quote_server_status()
        return {"data": _numpy_to_python(status)}
    except Exception as e:
        return {"error": str(e)}
