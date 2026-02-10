"""QMT Bridge — HTTP/WebSocket bridge for miniQMT market data & trading."""

from qmt_bridge._version import __version__
from qmt_bridge.client import QMTClient

__all__ = ["QMTClient", "__version__"]
