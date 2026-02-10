# QMT Bridge

> 将 miniQMT 的行情与交易能力通过 HTTP/WebSocket 接口暴露给局域网内的任意设备，让你在 Mac/Linux 上也能自由使用 A 股实时行情、历史数据和程序化交易。

**QMT Bridge** 是一个轻量级 API 服务，封装了 [xtquant](https://dict.thinktrader.net/nativeApi/start_now.html)（miniQMT 的 Python 库），将行情数据和交易功能以标准 HTTP/WebSocket 端点暴露出来。它运行在你的 Windows 机器上（QMT 客户端旁），允许局域网内任何设备（Mac、Linux 或手机）访问实时行情、历史 K 线、板块数据、交易等功能。

```
Mac / Linux (主力机)                    Windows (中转站)
┌──────────────────────┐                ┌─────────────────────────┐
│  你的分析 / 交易代码    │   HTTP/WS     │  miniQMT 客户端 (登录中)  │
│  本地数据库            │ ◄───────────► │  QMT Bridge (FastAPI)    │
│  可视化仪表盘          │   局域网       │  xtquant                 │
└──────────────────────┘                └─────────────────────────┘
```

## 核心特性

- **100+ REST API 端点** — 历史 K 线、实时行情、L2 逐笔、板块管理、财务数据、指数权重、期权链、可转债、ETF、港股通、期货主力合约等
- **5 个 WebSocket 端点** — 实时行情推送、全市场行情、L2 千档、下载进度、交易回报
- **程序化交易** (可选) — 下单、撤单、批量委托、融资融券、银证转账、智能交易
- **零依赖客户端** — Python 客户端基于 stdlib，无需安装 xtquant 即可在任意平台使用
- **API Key 认证** — 可选的 API Key 保护，交易端点强制认证

## 快速导航

| 文档 | 说明 |
|------|------|
| [快速开始](getting-started.md) | 安装、配置、启动服务 |
| [配置参考](configuration.md) | 所有配置项详解 |
| [REST API 速查](rest-api.md) | 全部 HTTP 端点列表 |
| [WebSocket](websocket.md) | WebSocket 端点使用指南 |
| [Python 客户端 API](api/index.md) | `QMTClient` 完整 API 参考 |

## 安装

```bash
git clone https://github.com/qmt-bridge/qmt-bridge.git
cd qmt-bridge

# 安装服务端（含 WebSocket 支持）
pip install -e ".[full]"

# 或者只安装客户端（零依赖）
pip install -e .

# 含 WebSocket 订阅支持
pip install -e ".[client]"
```

## 许可

[MIT](https://github.com/qmt-bridge/qmt-bridge/blob/main/LICENSE)
