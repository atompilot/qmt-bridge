"""Router — Financial data endpoints /api/financial/*."""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _financial_data_to_records

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.get("/data")
def get_financial_data(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    tables: str = Query("", description="财务表名列表，逗号分隔，为空取全部"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    report_type: str = Query("report_time", description="报告类型: report_time/announce_time"),
):
    stock_list = [s.strip() for s in stocks.split(",")]
    table_list = [t.strip() for t in tables.split(",") if t.strip()] if tables else []
    raw = xtdata.get_financial_data(
        stock_list,
        table_list=table_list,
        start_time=start_time,
        end_time=end_time,
        report_type=report_type,
    )
    return {"data": _financial_data_to_records(raw)}
