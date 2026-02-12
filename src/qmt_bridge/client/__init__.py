"""QMT Bridge 客户端 — 跨平台 HTTP/WebSocket 客户端（无需安装 xtquant）。

通过 Mixin 组合模式将行情、交易、数据下载等功能拆分到独立模块，
最终由 ``QMTClient`` 类统一继承，对外提供完整的 API 访问能力。

架构说明:
    BaseClient 提供底层 HTTP 传输（_get/_post/_delete），所有 Mixin
    通过 self._get() 等方法与服务端通信，无需依赖 xtquant 库。
"""

from qmt_bridge.client.base import BaseClient
from qmt_bridge.client.market import MarketMixin
from qmt_bridge.client.tick import TickMixin
from qmt_bridge.client.sector import SectorMixin
from qmt_bridge.client.calendar import CalendarMixin
from qmt_bridge.client.financial import FinancialMixin
from qmt_bridge.client.instrument import InstrumentMixin
from qmt_bridge.client.option import OptionMixin
from qmt_bridge.client.etf import ETFMixin
from qmt_bridge.client.cb import CBMixin
from qmt_bridge.client.futures import FuturesMixin
from qmt_bridge.client.meta import MetaMixin
from qmt_bridge.client.download import DownloadMixin
from qmt_bridge.client.formula import FormulaMixin
from qmt_bridge.client.hk import HKMixin
from qmt_bridge.client.tabular import TabularMixin
from qmt_bridge.client.utility import UtilityMixin
from qmt_bridge.client.trading import TradingMixin
from qmt_bridge.client.credit import CreditMixin
from qmt_bridge.client.fund import FundMixin
from qmt_bridge.client.smt import SMTMixin
from qmt_bridge.client.bank import BankMixin
from qmt_bridge.client.websocket import WebSocketMixin


class QMTClient(
    MarketMixin,
    TickMixin,
    SectorMixin,
    CalendarMixin,
    FinancialMixin,
    InstrumentMixin,
    OptionMixin,
    ETFMixin,
    CBMixin,
    FuturesMixin,
    MetaMixin,
    DownloadMixin,
    FormulaMixin,
    HKMixin,
    TabularMixin,
    UtilityMixin,
    TradingMixin,
    CreditMixin,
    FundMixin,
    SMTMixin,
    BankMixin,
    WebSocketMixin,
    BaseClient,
):
    """QMT Bridge 全功能客户端。

    通过 HTTP 请求与 QMT Bridge 服务端通信，封装了行情查询、数据下载、
    交易委托、两融业务、银证转账等全部功能。

    行情数据类方法无需认证即可使用；交易类方法需要提供 API Key。

    示例::

        from qmt_bridge import QMTClient

        # 仅查询行情（无需 API Key）
        client = QMTClient("192.168.1.100")
        df = client.get_history("000001.SZ", period="1d", count=60)

        # 交易操作（需要 API Key）
        client = QMTClient("192.168.1.100", api_key="your-key")
        result = client.place_order("000001.SZ", order_type=23, order_volume=100)
    """


__all__ = ["QMTClient"]
