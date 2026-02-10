"""Format trading events into Feishu interactive card messages."""

from __future__ import annotations

# Header color mapping (Feishu template_color)
_COLORS: dict[str, str] = {
    "trade": "green",
    "order": "blue",
    "order_error": "red",
    "cancel_error": "red",
    "connected": "green",
    "disconnected": "red",
    "asset": "blue",
    "position": "blue",
    "account_status": "blue",
    "test": "turquoise",
}

_TITLES: dict[str, str] = {
    "trade": "成交通知",
    "order": "委托更新",
    "order_error": "委托错误",
    "cancel_error": "撤单失败",
    "connected": "交易连接",
    "disconnected": "连接断开",
    "asset": "资产变动",
    "position": "持仓变动",
    "account_status": "账户状态",
    "test": "测试通知",
}

# order_type mapping
_ORDER_TYPE_MAP: dict[int, str] = {
    23: "买入",
    24: "卖出",
}


def _field(label: str, value: object) -> dict:
    """Build a single Feishu card field element."""
    return {
        "is_short": True,
        "text": {
            "tag": "lark_md",
            "content": f"**{label}：**{value}",
        },
    }


def _build_fields(event: dict) -> list[dict]:
    """Build card fields list based on event type."""
    etype = event.get("type", "")
    data: dict = event.get("data", {})

    if etype == "trade":
        direction = _ORDER_TYPE_MAP.get(data.get("order_type"), str(data.get("order_type", "")))
        amount = (data.get("traded_volume", 0) or 0) * (data.get("traded_price", 0) or 0)
        return [
            _field("股票", data.get("stock_code", "")),
            _field("方向", direction),
            _field("成交量", data.get("traded_volume", "")),
            _field("成交价", data.get("traded_price", "")),
            _field("成交金额", f"{amount:.2f}"),
            _field("委托编号", data.get("order_id", "")),
        ]

    if etype == "order":
        direction = _ORDER_TYPE_MAP.get(data.get("order_type"), str(data.get("order_type", "")))
        return [
            _field("股票", data.get("stock_code", "")),
            _field("方向", direction),
            _field("委托量", data.get("order_volume", "")),
            _field("委托价", data.get("price", "")),
            _field("已成交", data.get("traded_volume", "")),
            _field("状态", data.get("status_msg", data.get("order_status", ""))),
        ]

    if etype in ("order_error", "cancel_error"):
        return [
            _field("委托编号", data.get("order_id", "")),
            _field("错误代码", data.get("error_id", "")),
            _field("错误消息", data.get("error_msg", "")),
        ]

    if etype in ("connected", "disconnected"):
        return [_field("状态", "已连接" if etype == "connected" else "已断开")]

    if etype == "asset":
        return [
            _field("总资产", data.get("total_asset", "")),
            _field("可用资金", data.get("cash", "")),
            _field("冻结资金", data.get("frozen_cash", "")),
            _field("持仓市值", data.get("market_value", "")),
        ]

    if etype == "position":
        return [
            _field("股票", data.get("stock_code", "")),
            _field("持仓", data.get("volume", "")),
            _field("可用", data.get("can_use_volume", "")),
            _field("市值", data.get("market_value", "")),
        ]

    if etype == "account_status":
        return [_field("状态", data.get("status", ""))]

    if etype == "test":
        return [_field("消息", data.get("message", ""))]

    # Fallback: render all data fields
    return [_field(k, v) for k, v in data.items()] if data else []


def format_feishu_card(event: dict) -> dict:
    """Build a complete Feishu interactive card message body."""
    etype = event.get("type", "unknown")
    title = _TITLES.get(etype, f"通知 ({etype})")
    color = _COLORS.get(etype, "blue")
    fields = _build_fields(event)

    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {"tag": "plain_text", "content": f"📌 {title}"},
                "template": color,
            },
            "elements": [
                {
                    "tag": "div",
                    "fields": fields,
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": "QMT Bridge",
                        }
                    ],
                },
            ],
        },
    }
