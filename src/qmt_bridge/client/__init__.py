"""QMT Bridge client — cross-platform HTTP/WebSocket client (no xtquant needed)."""

from qmt_bridge.client.base import BaseClient
from qmt_bridge.client.market import MarketMixin
from qmt_bridge.client.tick import TickMixin
from qmt_bridge.client.sector import SectorMixin
from qmt_bridge.client.calendar import CalendarMixin
from qmt_bridge.client.financial import FinancialMixin
from qmt_bridge.client.instrument import InstrumentMixin
from qmt_bridge.client.option import OptionMixin
from qmt_bridge.client.etf import ETFMixin
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
    """Full-featured QMT Bridge client.

    Usage::

        from qmt_bridge import QMTClient

        client = QMTClient("192.168.1.100")
        df = client.get_history("000001.SZ", period="1d", count=60)

        # Trading requires API Key
        client = QMTClient("192.168.1.100", api_key="your-key")
    """


__all__ = ["QMTClient"]
