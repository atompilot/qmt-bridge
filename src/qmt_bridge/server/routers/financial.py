"""财务数据路由模块 /api/financial/*。

提供上市公司财务报表数据查询端点。
底层调用 xtquant.xtdata 的财务数据接口：
- xtdata.get_financial_data()  — 获取财务报表数据（利润表、资产负债表、现金流量表等）
"""

from fastapi import APIRouter, Query
from xtquant import xtdata

from ..helpers import _financial_data_to_records, _numpy_to_python

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.get("/data")
def get_financial_data(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    tables: str = Query("", description="财务表名列表，逗号分隔，为空取全部"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    report_type: str = Query("report_time", description="报告类型: report_time/announce_time"),
):
    """获取上市公司财务报表数据。

    支持查询利润表、资产负债表、现金流量表等多种财务报表。

    Args:
        stocks: 逗号分隔的股票代码列表。
        tables: 逗号分隔的财务表名列表，为空获取全部表。
            常用表名如: Balance（资产负债表）、Income（利润表）、CashFlow（现金流量表）。
        start_time: 开始时间。
        end_time: 结束时间。
        report_type: 报告类型，report_time 按报告期查询，announce_time 按公告日查询。

    Returns:
        data: 按股票代码分组的财务报表记录。

    底层调用: xtdata.get_financial_data(stock_list, table_list=..., ...)
    """
    # 将逗号分隔的字符串转换为列表
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


@router.get("/data_ori")
def get_financial_data_ori(
    stocks: str = Query(..., description="股票代码列表，逗号分隔"),
    tables: str = Query("", description="财务表名列表，逗号分隔"),
    start_time: str = Query("", description="开始时间"),
    end_time: str = Query("", description="结束时间"),
    report_type: str = Query("report_time", description="报告类型"),
):
    """获取原始格式财务数据 → xtdata.get_financial_data_ori()"""
    stock_list = [s.strip() for s in stocks.split(",")]
    table_list = [t.strip() for t in tables.split(",") if t.strip()] if tables else []
    raw = xtdata.get_financial_data_ori(
        stock_list,
        table_list=table_list,
        start_time=start_time,
        end_time=end_time,
        report_type=report_type,
    )
    return {"data": _numpy_to_python(raw)}
