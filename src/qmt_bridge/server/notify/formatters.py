"""飞书交互式卡片消息格式化器。

本模块负责将交易事件字典转换为飞书（Lark）交互式卡片消息格式。
不同类型的交易事件（成交、委托、错误、资产变动等）会被格式化为
结构化的卡片字段，在飞书群聊中以美观的方式展示。

消息结构：
    - 卡片头部：带颜色的标题（根据事件类型不同显示不同颜色）
    - 卡片内容：多列字段展示事件详情
    - 卡片底部：QMT Bridge 来源标注
"""

from __future__ import annotations

# 卡片头部颜色映射（飞书 template_color 参数）
# 绿色表示积极事件，红色表示错误/断开，蓝色表示信息类事件
_COLORS: dict[str, str] = {
    "trade": "green",           # 成交 — 绿色
    "order": "blue",            # 委托更新 — 蓝色
    "order_error": "red",       # 委托错误 — 红色
    "cancel_error": "red",      # 撤单失败 — 红色
    "connected": "green",       # 连接建立 — 绿色
    "disconnected": "red",      # 连接断开 — 红色
    "asset": "blue",            # 资产变动 — 蓝色
    "position": "blue",         # 持仓变动 — 蓝色
    "account_status": "blue",   # 账户状态 — 蓝色
    "test": "turquoise",        # 测试通知 — 青绿色
}

# 卡片标题文本映射
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

# 委托类型数值到中文名称的映射
_ORDER_TYPE_MAP: dict[int, str] = {
    23: "买入",
    24: "卖出",
}


def _field(label: str, value: object) -> dict:
    """构建飞书卡片的单个字段元素。

    使用 lark_md 标签支持 Markdown 粗体显示标签名。

    Args:
        label: 字段标签（如"股票"、"成交价"）。
        value: 字段值。

    Returns:
        飞书卡片字段字典，设置 is_short=True 以支持多列显示。
    """
    return {
        "is_short": True,
        "text": {
            "tag": "lark_md",
            "content": f"**{label}：**{value}",
        },
    }


def _build_fields(event: dict) -> list[dict]:
    """根据事件类型构建对应的卡片字段列表。

    不同事件类型展示不同的字段内容：
    - trade: 股票、方向、成交量、成交价、成交金额、委托编号
    - order: 股票、方向、委托量、委托价、已成交量、状态
    - order_error/cancel_error: 委托编号、错误代码、错误消息
    - asset: 总资产、可用资金、冻结资金、持仓市值
    - position: 股票、持仓量、可用量、市值
    - 其他: 回退到展示所有 data 字段

    Args:
        event: 交易事件字典，包含 'type' 和 'data' 字段。

    Returns:
        飞书卡片字段列表。
    """
    etype = event.get("type", "")
    data: dict = event.get("data", {})

    if etype == "trade":
        # 成交通知：展示成交详情
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
        # 委托更新：展示委托详情和当前状态
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
        # 错误通知：展示错误详情
        return [
            _field("委托编号", data.get("order_id", "")),
            _field("错误代码", data.get("error_id", "")),
            _field("错误消息", data.get("error_msg", "")),
        ]

    if etype in ("connected", "disconnected"):
        # 连接状态通知
        return [_field("状态", "已连接" if etype == "connected" else "已断开")]

    if etype == "asset":
        # 资产变动通知
        return [
            _field("总资产", data.get("total_asset", "")),
            _field("可用资金", data.get("cash", "")),
            _field("冻结资金", data.get("frozen_cash", "")),
            _field("持仓市值", data.get("market_value", "")),
        ]

    if etype == "position":
        # 持仓变动通知
        return [
            _field("股票", data.get("stock_code", "")),
            _field("持仓", data.get("volume", "")),
            _field("可用", data.get("can_use_volume", "")),
            _field("市值", data.get("market_value", "")),
        ]

    if etype == "account_status":
        # 账户状态通知
        return [_field("状态", data.get("status", ""))]

    if etype == "test":
        # 测试通知
        return [_field("消息", data.get("message", ""))]

    # 回退策略：将 data 中的所有字段逐一展示
    return [_field(k, v) for k, v in data.items()] if data else []


def format_feishu_card(event: dict) -> dict:
    """将交易事件构建为完整的飞书交互式卡片消息体。

    生成的消息结构：
    - msg_type: "interactive"（交互式卡片）
    - card.header: 带颜色的标题
    - card.elements[0]: 字段区域（div），展示事件详情
    - card.elements[1]: 底部备注（note），标注来源

    Args:
        event: 交易事件字典，包含 'type' 和可选的 'data' 字段。

    Returns:
        符合飞书 Webhook API 规范的消息体字典，可直接作为 POST 请求的 JSON 发送。
    """
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
