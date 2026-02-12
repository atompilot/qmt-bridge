"""TickMixin — Level-2 逐笔/Tick 数据客户端方法。

封装了 Level-2 行情数据的查询接口，包括：
- L2 逐笔行情（quote）、逐笔委托（order）、逐笔成交（transaction）
- 千档行情（thousand）— 买卖各1000档的盘口数据

底层对应 xtquant 的 ``xtdata.get_l2_quote()``、``xtdata.get_l2_order()`` 等函数。

注意: L2 数据需要开通 Level-2 行情权限才能获取。
"""


class TickMixin:
    """Level-2/Tick 数据客户端方法集合，对应 /api/tick/* 端点。"""

    def get_l2_quote(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """获取 L2 逐笔行情快照。

        底层调用 ``xtdata.get_l2_quote()``，返回包含最新价、买卖盘口、
        成交量等逐笔级别的行情快照数据。

        Args:
            stock: 股票代码，如 ``"000001.SZ"``
            start_time: 开始时间，格式 ``"20230101093000"``
            end_time: 结束时间
            count: 返回条数，-1 表示返回范围内全部数据

        Returns:
            L2 行情快照数据字典
        """
        resp = self._get("/api/tick/l2_quote", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_order(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """获取 L2 逐笔委托数据。

        底层调用 ``xtdata.get_l2_order()``，返回交易所发布的逐笔委托明细，
        包含每一笔买入/卖出委托的价格、数量和时间等信息。

        Args:
            stock: 股票代码
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部

        Returns:
            逐笔委托数据字典
        """
        resp = self._get("/api/tick/l2_order", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_transaction(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """获取 L2 逐笔成交数据。

        底层调用 ``xtdata.get_l2_transaction()``，返回交易所发布的逐笔成交明细，
        包含每一笔实际成交的价格、数量、买卖方向和时间等信息。

        Args:
            stock: 股票代码
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部

        Returns:
            逐笔成交数据字典
        """
        resp = self._get("/api/tick/l2_transaction", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_thousand_quote(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """获取 L2 千档行情快照。

        底层调用 ``xtdata.get_l2_thousand_quote()``，返回买卖各1000档的
        盘口报价数据，适合深度分析市场流动性和订单簿结构。

        Args:
            stock: 股票代码
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部

        Returns:
            千档行情数据字典
        """
        resp = self._get("/api/tick/l2_thousand_quote", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_thousand_orderbook(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """获取 L2 千档委托簿数据。

        底层调用 ``xtdata.get_l2_thousand_orderbook()``，返回买卖各1000档
        的委托簿完整快照，包含各档位的价格和挂单量。

        Args:
            stock: 股票代码
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部

        Returns:
            千档委托簿数据字典
        """
        resp = self._get("/api/tick/l2_thousand_orderbook", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_thousand_trade(
        self, stock: str, start_time: str = "", end_time: str = "", count: int = -1
    ) -> dict:
        """获取 L2 千档成交数据。

        底层调用 ``xtdata.get_l2_thousand_trade()``，返回千档级别的
        成交汇总数据。

        Args:
            stock: 股票代码
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部

        Returns:
            千档成交数据字典
        """
        resp = self._get("/api/tick/l2_thousand_trade", {
            "stock": stock,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
        })
        return resp.get("data", {})

    def get_l2_thousand_queue(self, stock: str) -> dict:
        """获取 L2 千档队列数据。

        Args:
            stock: 股票代码

        Returns:
            千档队列数据字典
        """
        resp = self._get("/api/tick/l2_thousand_queue", {"stock": stock})
        return resp.get("data", {})

    def get_broker_queue(self, stock: str) -> dict:
        """获取经纪商队列数据。

        Args:
            stock: 股票代码

        Returns:
            经纪商队列数据字典
        """
        resp = self._get("/api/tick/broker_queue", {"stock": stock})
        return resp.get("data", {})

    def get_order_rank(self, stock: str) -> dict:
        """获取委托排名数据。

        Args:
            stock: 股票代码

        Returns:
            委托排名数据字典
        """
        resp = self._get("/api/tick/order_rank", {"stock": stock})
        return resp.get("data", {})
