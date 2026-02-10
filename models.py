"""QMT Bridge — Pydantic request models."""

from pydantic import BaseModel


class DownloadRequest(BaseModel):
    stock: str
    period: str = "1d"
    start: str = ""
    end: str = ""


class BatchDownloadRequest(BaseModel):
    stocks: list[str]
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""


class FinancialDownldadadRequest(BaseModel):
    stocks: list[str]
    tables: list[str] = []
    start_time: str = ""
    end_time: str = ""
