"""Router — Data download endpoints /api/download/*."""

from fastapi import APIRouter
from xtquant import xtdata

from ..models import BatchDownloadRequest, FinancialDownload2Request, FinancialDownloadRequest

router = APIRouter(prefix="/api/download", tags=["download"])


@router.post("/batch")
def download_batch(req: BatchDownloadRequest):
    xtdata.download_history_data2(
        req.stocks,
        period=req.period,
        start_time=req.start_time,
        end_time=req.end_time,
    )
    return {"status": "ok", "stocks": req.stocks, "period": req.period}


@router.post("/financial")
def download_financial(req: FinancialDownloadRequest):
    xtdata.download_financial_data(
        req.stocks,
        table_list=req.tables,
        start_time=req.start_time,
        end_time=req.end_time,
    )
    return {"status": "ok", "stocks": req.stocks, "tables": req.tables}


@router.post("/sector_data")
def download_sector_data():
    xtdata.download_sector_data()
    return {"status": "ok"}


@router.post("/index_weight")
def download_index_weight():
    xtdata.download_index_weight()
    return {"status": "ok"}


@router.post("/etf_info")
def download_etf_info():
    xtdata.download_etf_info()
    return {"status": "ok"}


@router.post("/cb_data")
def download_cb_data():
    xtdata.download_cb_data()
    return {"status": "ok"}


@router.post("/history_contracts")
def download_history_contracts():
    xtdata.download_history_contracts()
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# New download endpoints (Step 5)
# ---------------------------------------------------------------------------


@router.post("/ipo_data")
def download_ipo_data():
    """Trigger IPO data download."""
    xtdata.download_ipo_data()
    return {"status": "ok"}


@router.post("/option_data")
def download_option_data():
    """Trigger option data download."""
    xtdata.download_option_data()
    return {"status": "ok"}


@router.post("/futures_data")
def download_futures_data():
    """Trigger futures data download."""
    xtdata.download_futures_data()
    return {"status": "ok"}


@router.post("/financial2")
def download_financial_data2(req: FinancialDownload2Request):
    """Synchronous financial data download (blocks until complete)."""
    xtdata.download_financial_data2(
        req.stocks,
        table_list=req.tables,
    )
    return {"status": "ok", "stocks": req.stocks, "tables": req.tables}


@router.post("/holiday")
def download_holiday_data():
    """Download holiday calendar data."""
    xtdata.download_holiday_data()
    return {"status": "ok"}
