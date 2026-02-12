"""Pydantic 请求/响应模型定义模块。

本模块定义了 QMT Bridge 所有 REST API 端点的请求体模型（Request Models）。
这些模型基于 Pydantic BaseModel，FastAPI 会自动完成 JSON 反序列化和参数校验。

所有模型字段严格对齐 xtquant 原始 API 参数命名。
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 数据下载模型
# ---------------------------------------------------------------------------

class DownloadRequest(BaseModel):
    """单只股票历史数据下载请求。"""
    stock: str
    period: str = "1d"
    start: str = ""
    end: str = ""


class BatchDownloadRequest(BaseModel):
    """批量股票历史数据下载请求。"""
    stock_list: list[str] = Field(default=[], alias="stocks")
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""

    model_config = {"populate_by_name": True}


class FinancialDownloadRequest(BaseModel):
    """财务数据下载请求。"""
    stock_list: list[str] = Field(default=[], alias="stocks")
    table_list: list[str] = Field(default=[], alias="tables")
    start_time: str = ""
    end_time: str = ""

    model_config = {"populate_by_name": True}


class FinancialDownload2Request(BaseModel):
    """财务数据下载请求（第二版接口）。"""
    stock_list: list[str] = Field(default=[], alias="stocks")
    table_list: list[str] = Field(default=[], alias="tables")

    model_config = {"populate_by_name": True}


class HisSTDataDownloadRequest(BaseModel):
    """历史 ST 数据下载请求。"""
    stock_list: list[str] = Field(default=[], alias="stocks")
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""

    model_config = {"populate_by_name": True}


class TabularDataDownloadRequest(BaseModel):
    """表格数据下载请求。"""
    table_list: list[str] = Field(default=[], alias="tables")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# 板块管理模型
# ---------------------------------------------------------------------------

class CreateSectorFolderRequest(BaseModel):
    """创建板块分类文件夹请求。"""
    folder_name: str


class CreateSectorRequest(BaseModel):
    """创建自定义板块请求。"""
    sector_name: str
    parent_node: str = ""


class AddSectorStocksRequest(BaseModel):
    """向板块添加成分股请求。"""
    sector_name: str
    stock_list: list[str] = Field(default=[], alias="stocks")

    model_config = {"populate_by_name": True}


class RemoveSectorStocksRequest(BaseModel):
    """从板块移除成分股请求。"""
    sector_name: str
    stock_list: list[str] = Field(default=[], alias="stocks")

    model_config = {"populate_by_name": True}


class ResetSectorRequest(BaseModel):
    """重置板块成分股请求。"""
    sector_name: str
    stock_list: list[str] = Field(default=[], alias="stocks")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# 普通交易委托模型
# ---------------------------------------------------------------------------

class OrderRequest(BaseModel):
    """股票委托下单请求。"""
    account_id: str = ""
    stock_code: str
    order_type: int
    order_volume: int
    price_type: int = 5
    price: float = 0.0
    strategy_name: str = ""
    order_remark: str = ""


class CancelRequest(BaseModel):
    """撤单请求。"""
    account_id: str = ""
    order_id: int


class CancelBySysidRequest(BaseModel):
    """按系统编号撤单请求。"""
    account_id: str = ""
    market: str
    sysid: str


class QueryOrderRequest(BaseModel):
    """查询委托单请求。"""
    account_id: str = ""
    cancelable_only: bool = False


class QueryPositionRequest(BaseModel):
    """查询持仓请求。"""
    account_id: str = ""


class QueryAssetRequest(BaseModel):
    """查询资产请求。"""
    account_id: str = ""


# ---------------------------------------------------------------------------
# 信用交易（融资融券）模型
# ---------------------------------------------------------------------------

class CreditOrderRequest(BaseModel):
    """信用交易委托请求（通过 order_type 常量区分融资/融券）。"""
    account_id: str = ""
    stock_code: str
    order_type: int
    order_volume: int
    price_type: int = 5
    price: float = 0.0
    strategy_name: str = ""
    order_remark: str = ""


# ---------------------------------------------------------------------------
# 资金划转模型
# ---------------------------------------------------------------------------

class FundTransferRequest(BaseModel):
    """资金划转请求。"""
    account_id: str = ""
    transfer_direction: int
    amount: float


# ---------------------------------------------------------------------------
# 银证转账模型（对齐 xttrader 真实 API）
# ---------------------------------------------------------------------------

class BankTransferRequest(BaseModel):
    """银证转账请求。"""
    account_id: str = ""
    bank_no: str
    bank_account: str
    balance: float
    bank_pwd: str = ""
    fund_pwd: str = ""


class BankAmountQueryRequest(BaseModel):
    """银行余额查询请求（含密码，故用 POST）。"""
    account_id: str = ""
    bank_no: str
    bank_account: str
    bank_pwd: str


class BankTransferStreamRequest(BaseModel):
    """银证转账流水查询请求。"""
    account_id: str = ""
    start_date: str
    end_date: str
    bank_no: str = ""
    bank_account: str = ""


# ---------------------------------------------------------------------------
# CTP 跨市场资金划转模型
# ---------------------------------------------------------------------------

class CTPCrossMarketTransferRequest(BaseModel):
    """CTP 跨市场资金划转请求（期权/期货双账户）。"""
    opt_account_id: str
    ft_account_id: str
    balance: float


# ---------------------------------------------------------------------------
# 证券划转模型
# ---------------------------------------------------------------------------

class SecuTransferRequest(BaseModel):
    """证券划转请求。"""
    account_id: str = ""
    transfer_direction: int
    stock_code: str
    volume: int
    transfer_type: int


# ---------------------------------------------------------------------------
# 转融通（SMT）模型
# ---------------------------------------------------------------------------

class SMTNegotiateOrderRequest(BaseModel):
    """转融通协商成交委托请求（对齐 xttrader 真实参数）。"""
    account_id: str = ""
    src_group_id: str
    order_code: str
    date: str
    amount: float
    apply_rate: float
    dict_param: dict = {}


class SMTAppointmentOrderRequest(BaseModel):
    """转融通预约委托请求。"""
    account_id: str = ""
    order_code: str
    date: str
    amount: float
    apply_rate: float


class SMTAppointmentCancelRequest(BaseModel):
    """转融通预约取消请求。"""
    account_id: str = ""
    apply_id: str


class SMTCompactRenewalRequest(BaseModel):
    """转融通合约展期请求。"""
    account_id: str = ""
    cash_compact_id: str
    order_code: str
    defer_days: int
    defer_num: int
    apply_rate: float


class SMTCompactReturnRequest(BaseModel):
    """转融通合约归还请求。"""
    account_id: str = ""
    src_group_id: str
    cash_compact_id: str
    order_code: str
    occur_amount: float


class SMTQueryRequest(BaseModel):
    """转融通账户查询请求。"""
    account_id: str = ""


# ---------------------------------------------------------------------------
# 公式/模型计算模型
# ---------------------------------------------------------------------------

class CallFormulaRequest(BaseModel):
    """单只股票公式计算请求。"""
    formula_name: str
    stock_code: str
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""
    count: int = -1
    dividend_type: str = "none"
    params: dict = {}


class CallFormulaBatchRequest(BaseModel):
    """批量股票公式计算请求。"""
    formula_name: str
    stock_codes: list[str]
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""
    count: int = -1
    dividend_type: str = "none"
    params: dict = {}


class GenerateIndexDataRequest(BaseModel):
    """自定义指数数据生成请求。"""
    index_code: str
    stock_list: list[str] = Field(default=[], alias="stocks")
    weights: list[float]
    period: str = "1d"
    start_time: str = ""
    end_time: str = ""

    model_config = {"populate_by_name": True}


class CreateFormulaRequest(BaseModel):
    """创建公式请求。"""
    formula_name: str
    formula_file: str
    formula_type: str = ""


class ImportFormulaRequest(BaseModel):
    """导入公式请求。"""
    formula_file: str


# ---------------------------------------------------------------------------
# 异步委托模型
# ---------------------------------------------------------------------------

class AsyncOrderRequest(BaseModel):
    """异步委托下单请求。"""
    account_id: str = ""
    stock_code: str
    order_type: int
    order_volume: int
    price_type: int = 5
    price: float = 0.0
    strategy_name: str = ""
    order_remark: str = ""


class AsyncCancelRequest(BaseModel):
    """异步撤单请求。"""
    account_id: str = ""
    order_id: int


# ---------------------------------------------------------------------------
# 数据导出/同步模型（对齐 xttrader 真实签名）
# ---------------------------------------------------------------------------

class ExportDataRequest(BaseModel):
    """数据导出请求。"""
    account_id: str = ""
    result_path: str
    data_type: str
    start_time: str = ""
    end_time: str = ""
    user_param: str = ""


class QueryDataRequest(BaseModel):
    """数据查询请求。"""
    account_id: str = ""
    result_path: str
    data_type: str
    start_time: str = ""
    end_time: str = ""
    user_param: str = ""


class SyncTransactionRequest(BaseModel):
    """交易数据同步请求。"""
    account_id: str = ""
    operation: str
    data_type: str
    deal_list: list[dict] = []
