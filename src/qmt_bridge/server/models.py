"""QMT Bridge — Pydantic request/response models."""

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Legacy / Download models
# ---------------------------------------------------------------------------

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


class FinancialDownloadRequest(BaseModel):
    stocks: list[str]
    tables: list[str] = []
    start_time: str = ""
    end_time: str = ""


# ---------------------------------------------------------------------------
# Sector write models
# ---------------------------------------------------------------------------

class CreateSectorFolderRequest(BaseModel):
    folder_name: str


class CreateSectorRequest(BaseModel):
    sector_name: str
    parent_node: str = ""


class AddSectorStocksRequest(BaseModel):
    sector_name: str
    stocks: list[str]


class RemoveSectorStocksRequest(BaseModel):
    sector_name: str
    stocks: list[str]


class ResetSectorRequest(BaseModel):
    sector_name: str
    stocks: list[str]


# ---------------------------------------------------------------------------
# Trading models
# ---------------------------------------------------------------------------

class OrderRequest(BaseModel):
    account_id: str = ""
    stock_code: str
    order_type: int  # xtconstant order type
    order_volume: int
    price_type: int = 5  # LATEST_PRICE
    price: float = 0.0
    strategy_name: str = ""
    order_remark: str = ""


class CancelRequest(BaseModel):
    account_id: str = ""
    order_id: int


class QueryOrderRequest(BaseModel):
    account_id: str = ""
    cancelable_only: bool = False


class QueryPositionRequest(BaseModel):
    account_id: str = ""


class QueryAssetRequest(BaseModel):
    account_id: str = ""


# ---------------------------------------------------------------------------
# Credit trading models
# ---------------------------------------------------------------------------

class CreditOrderRequest(BaseModel):
    account_id: str = ""
    stock_code: str
    order_type: int
    order_volume: int
    price_type: int = 5
    price: float = 0.0
    credit_type: str = "fin_buy"  # fin_buy / slo_sell / buy_back / sell_back
    strategy_name: str = ""
    order_remark: str = ""


class CreditQueryRequest(BaseModel):
    account_id: str = ""


# ---------------------------------------------------------------------------
# Fund transfer models
# ---------------------------------------------------------------------------

class FundTransferRequest(BaseModel):
    account_id: str = ""
    transfer_direction: int  # 0: in, 1: out
    amount: float


class BankTransferRequest(BaseModel):
    account_id: str = ""
    transfer_direction: int
    amount: float
    bank_code: str = ""


# ---------------------------------------------------------------------------
# SMT models
# ---------------------------------------------------------------------------

class SMTOrderRequest(BaseModel):
    account_id: str = ""
    stock_code: str
    order_type: int
    order_volume: int
    price_type: int = 5
    price: float = 0.0
    smt_type: str = ""
    strategy_name: str = ""
    order_remark: str = ""


class SMTQueryRequest(BaseModel):
    account_id: str = ""


# ---------------------------------------------------------------------------
# Formula / Model API models
# ---------------------------------------------------------------------------

class CallFormulaRequest(BaseModel):
    formula_name: str
    stock_code: str
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""
    count: int = -1
    dividend_type: str = "none"
    params: dict = {}


class CallFormulaBatchRequest(BaseModel):
    formula_name: str
    stock_codes: list[str]
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""
    count: int = -1
    dividend_type: str = "none"
    params: dict = {}


class GenerateIndexDataRequest(BaseModel):
    index_code: str
    stocks: list[str]
    weights: list[float]
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""


# ---------------------------------------------------------------------------
# Additional download models
# ---------------------------------------------------------------------------

class FinancialDownload2Request(BaseModel):
    stocks: list[str]
    tables: list[str] = []


# ---------------------------------------------------------------------------
# Async order models
# ---------------------------------------------------------------------------

class AsyncOrderRequest(BaseModel):
    account_id: str = ""
    stock_code: str
    order_type: int
    order_volume: int
    price_type: int = 5
    price: float = 0.0
    strategy_name: str = ""
    order_remark: str = ""


class AsyncCancelRequest(BaseModel):
    account_id: str = ""
    order_id: int


# ---------------------------------------------------------------------------
# Export / Sync models
# ---------------------------------------------------------------------------

class ExportDataRequest(BaseModel):
    account_id: str = ""
    data_type: str = "orders"
    file_path: str = ""


class SyncTransactionRequest(BaseModel):
    account_id: str = ""
    data: list[dict] = []


# ---------------------------------------------------------------------------
# CTP cross-market transfer models
# ---------------------------------------------------------------------------

class CTPCrossMarketTransferRequest(BaseModel):
    account_id: str = ""
    amount: float


# ---------------------------------------------------------------------------
# SMT appointment / negotiate models
# ---------------------------------------------------------------------------

class SMTNegotiateOrderRequest(BaseModel):
    account_id: str = ""
    stock_code: str
    order_type: int
    order_volume: int
    price: float = 0.0
    compact_id: str = ""
    strategy_name: str = ""
    order_remark: str = ""
