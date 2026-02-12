"""QMT Bridge — 基于 HTTP/WebSocket 的 miniQMT 行情与交易桥接服务。

本包将迅投 miniQMT (xtquant) 的行情数据和交易能力封装为 RESTful API 和
WebSocket 推送接口，使得任意编程语言或平台都能通过网络访问 QMT 的数据和交易功能。

主要组件:
    - ``QMTClient``: 跨平台 HTTP/WebSocket 客户端，无需安装 xtquant 即可使用
    - ``qmt_bridge.server``: FastAPI 服务端，运行在安装了 xtquant 的 Windows 机器上
"""

from qmt_bridge._version import __version__
from qmt_bridge.client import QMTClient

__all__ = ["QMTClient", "__version__"]
