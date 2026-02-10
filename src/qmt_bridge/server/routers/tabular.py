"""Router — Tabular data endpoints /api/tabular/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _numpy_to_python

router = APIRouter(prefix="/api/tabular", tags=["tabular"])


@router.get("/data")
def get_tabular_data(
    table_name: str = Query(..., description="表名"),
    stocks: str = Query("", description="股票代码列表，逗号分隔"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
):
    """Get data from a named tabular data source."""
    stock_list = [s.strip() for s in stocks.split(",") if s.strip()] if stocks else []
    raw = xtdata.get_financial_data(stock_list, table_list=[table_name], start_time=start_time, end_time=end_time)
    return {"table": table_name, "data": _numpy_to_python(raw)}


@router.get("/tables")
def list_tables():
    """List available tabular data tables."""
    try:
        tables = xtdata.get_financial_table_list()
        return {"tables": _numpy_to_python(tables)}
    except Exception:
        return {"tables": []}
