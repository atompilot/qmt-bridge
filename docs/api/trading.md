# 交易

下单、撤单、批量委托、持仓/资产/成交查询等交易功能。

!!! note "需要认证"
    交易方法需要在创建客户端时传入 `api_key` 参数。

```python
client = QMTClient(host="192.168.1.100", api_key="your-secret-key")
```

::: qmt_bridge.client.trading.TradingMixin
    options:
      show_root_heading: false
      heading_level: 2
