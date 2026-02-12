"""FormulaMixin — 公式/指标计算客户端方法。

封装了 xtquant 公式引擎相关的接口，支持调用预定义的技术指标公式
以及生成自定义指数数据。

底层对应 xtquant 的 ``xtdata.call_formula()`` 等函数。
"""


class FormulaMixin:
    """公式/指标计算客户端方法集合，对应 /api/formula/* 端点。"""

    def call_formula(
        self,
        formula_name: str,
        stock_code: str,
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        **params,
    ) -> dict:
        """对单只股票调用公式/指标计算。

        底层调用 ``xtdata.call_formula()``，使用 xtquant 内置的公式引擎
        计算技术指标。支持 MA、MACD、RSI、KDJ 等常用技术指标。

        Args:
            formula_name: 公式名称，如 ``"MA"``、``"MACD"``
            stock_code: 股票代码，如 ``"000001.SZ"``
            period: K 线周期
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数，-1 表示全部
            dividend_type: 除权类型
            **params: 公式额外参数（如 MA 的周期参数）

        Returns:
            公式计算结果字典
        """
        return self._post("/api/formula/call", {
            "formula_name": formula_name,
            "stock_code": stock_code,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "params": params,
        })

    def call_formula_batch(
        self,
        formula_name: str,
        stock_codes: list[str],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
        count: int = -1,
        dividend_type: str = "none",
        **params,
    ) -> dict:
        """对多只股票批量调用公式/指标计算。

        与 ``call_formula()`` 功能相同，但支持一次性对多只股票进行计算，
        避免逐个请求的网络开销。

        Args:
            formula_name: 公式名称
            stock_codes: 股票代码列表
            period: K 线周期
            start_time: 开始时间
            end_time: 结束时间
            count: 返回条数
            dividend_type: 除权类型
            **params: 公式额外参数

        Returns:
            以股票代码为键的计算结果字典
        """
        return self._post("/api/formula/call_batch", {
            "formula_name": formula_name,
            "stock_codes": stock_codes,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
            "count": count,
            "dividend_type": dividend_type,
            "params": params,
        })

    def generate_index_data(
        self,
        index_code: str,
        stocks: list[str],
        weights: list[float],
        period: str = "1d",
        start_time: str = "",
        end_time: str = "",
    ) -> dict:
        """生成自定义指数数据。

        根据指定的成分股列表和权重，合成自定义指数的行情数据。
        可用于构建行业指数、策略组合等场景。

        Args:
            index_code: 自定义指数代码标识
            stocks: 成分股代码列表
            weights: 各成分股的权重列表（与 stocks 一一对应）
            period: K 线周期
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            合成指数的行情数据字典
        """
        return self._post("/api/formula/generate_index_data", {
            "index_code": index_code,
            "stocks": stocks,
            "weights": weights,
            "period": period,
            "start_time": start_time,
            "end_time": end_time,
        })

    def create_formula(
        self, formula_name: str, formula_file: str, formula_type: str = ""
    ) -> dict:
        """创建公式。

        Args:
            formula_name: 公式名称
            formula_file: 公式文件路径
            formula_type: 公式类型

        Returns:
            创建结果
        """
        return self._post("/api/formula/create", {
            "formula_name": formula_name,
            "formula_file": formula_file,
            "formula_type": formula_type,
        })

    def import_formula(self, formula_file: str) -> dict:
        """导入公式。

        Args:
            formula_file: 公式文件路径

        Returns:
            导入结果
        """
        return self._post("/api/formula/import", {
            "formula_file": formula_file,
        })

    def del_formula(self, formula_name: str) -> dict:
        """删除公式。

        Args:
            formula_name: 公式名称

        Returns:
            删除结果
        """
        return self._delete("/api/formula/delete", {"formula_name": formula_name})

    def get_formulas(self) -> dict:
        """获取公式列表。

        Returns:
            公式列表
        """
        return self._get("/api/formula/list")
