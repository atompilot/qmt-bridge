"""XtTraderManager — XtQuantTrader 实例的生命周期管理器。

本模块提供 ``XtTraderManager`` 类，负责：
- 在 FastAPI 应用启动时初始化并连接 XtQuantTrader 实例
- 在应用关闭时断开连接并释放资源
- 封装所有交易操作（下单、撤单、查询、信用交易、银证转账等）

该管理器作为整个 qmt-bridge 服务端与 QMT 迅投客户端之间的桥梁，
所有 REST API 路由中的交易操作最终都委托给此类来执行。

所有方法签名严格对齐 xtquant.xttrader 的真实 API。
"""

import logging

logger = logging.getLogger("qmt_bridge.trading")


class XtTraderManager:
    """XtQuantTrader 实例管理器。

    在 FastAPI lifespan 启动阶段、当交易功能启用时被创建。
    负责维护与 QMT 迅投交易终端的连接，并提供统一的交易操作接口。

    Attributes:
        mini_qmt_path: MiniQMT 客户端安装路径，用于连接交易终端。
        account_id: 默认交易账户 ID。
    """

    def __init__(self, mini_qmt_path: str = "", account_id: str = ""):
        self.mini_qmt_path = mini_qmt_path
        self.account_id = account_id
        self._trader = None      # XtQuantTrader 实例，连接后赋值
        self._account = None     # 默认 StockAccount 实例

    def connect(self):
        """初始化并连接 XtQuantTrader 实例。"""
        from xtquant.xttrader import XtQuantTrader
        from xtquant.xttype import StockAccount

        from .callbacks import BridgeTraderCallback

        path = self.mini_qmt_path
        session_id = hash(path) & 0xFFFF

        self._trader = XtQuantTrader(path, session_id)
        self._account = StockAccount(self.account_id)
        self._callback = BridgeTraderCallback()

        self._trader.register_callback(self._callback)
        self._trader.start()

        result = self._trader.connect()
        if result != 0:
            raise RuntimeError(f"XtQuantTrader connect failed: {result}")

        result = self._trader.subscribe(self._account)
        if result != 0:
            logger.warning("subscribe_account returned %s", result)

        logger.info("XtQuantTrader connected, account=%s", self.account_id)

    def disconnect(self):
        """断开连接并清理资源。"""
        if self._trader is not None:
            try:
                self._trader.stop()
            except Exception:
                logger.exception("Error stopping XtQuantTrader")
            self._trader = None

    def _resolve_account(self, account_id: str = ""):
        """解析交易账户，返回 StockAccount 实例。"""
        if account_id and account_id != self.account_id:
            from xtquant.xttype import StockAccount
            return StockAccount(account_id)
        return self._account

    # ------------------------------------------------------------------
    # 委托操作
    # ------------------------------------------------------------------

    def order(self, stock_code: str, order_type: int, order_volume: int,
              price_type: int = 5, price: float = 0.0,
              strategy_name: str = "", order_remark: str = "",
              account_id: str = ""):
        """同步下单 → _trader.order_stock()"""
        account = self._resolve_account(account_id)
        return self._trader.order_stock(
            account, stock_code, order_type, order_volume,
            price_type, price, strategy_name, order_remark,
        )

    def order_async(self, stock_code: str, order_type: int, order_volume: int,
                    price_type: int = 5, price: float = 0.0,
                    strategy_name: str = "", order_remark: str = "",
                    account_id: str = ""):
        """异步下单 → _trader.order_stock_async()"""
        account = self._resolve_account(account_id)
        return self._trader.order_stock_async(
            account, stock_code, order_type, order_volume,
            price_type, price, strategy_name, order_remark,
        )

    def cancel_order(self, order_id: int, account_id: str = ""):
        """同步撤单 → _trader.cancel_order_stock()"""
        account = self._resolve_account(account_id)
        return self._trader.cancel_order_stock(account, order_id)

    def cancel_order_async(self, order_id: int, account_id: str = ""):
        """异步撤单 → _trader.cancel_order_stock_async()"""
        account = self._resolve_account(account_id)
        return self._trader.cancel_order_stock_async(account, order_id)

    def cancel_order_stock_sysid(self, market: str, sysid: str, account_id: str = ""):
        """按系统编号同步撤单 → _trader.cancel_order_stock_sysid()"""
        account = self._resolve_account(account_id)
        return self._trader.cancel_order_stock_sysid(account, market, sysid)

    def cancel_order_stock_sysid_async(self, market: str, sysid: str, account_id: str = ""):
        """按系统编号异步撤单 → _trader.cancel_order_stock_sysid_async()"""
        account = self._resolve_account(account_id)
        return self._trader.cancel_order_stock_sysid_async(account, market, sysid)

    # ------------------------------------------------------------------
    # 查询操作
    # ------------------------------------------------------------------

    def query_orders(self, account_id: str = "", cancelable_only: bool = False):
        """查询当日委托列表 → _trader.query_stock_orders()"""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_orders(account, cancelable_only)

    def query_positions(self, account_id: str = ""):
        """查询当前持仓列表 → _trader.query_stock_positions()"""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_positions(account)

    def query_asset(self, account_id: str = ""):
        """查询账户资产信息 → _trader.query_stock_asset()"""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_asset(account)

    def query_trades(self, account_id: str = ""):
        """查询当日成交列表 → _trader.query_stock_trades()"""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_trades(account)

    def query_order_detail(self, order_id: int = 0, account_id: str = ""):
        """根据委托编号查询单笔委托详情（遍历过滤）。"""
        account = self._resolve_account(account_id)
        orders = self._trader.query_stock_orders(account, False)
        if orders:
            for o in orders:
                if getattr(o, "order_id", None) == order_id:
                    return o
        return None

    def query_single_order(self, order_id: int, account_id: str = ""):
        """按委托编号查询单笔委托 → _trader.query_stock_order()"""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_order(account, order_id)

    def query_single_trade(self, trade_id: int, account_id: str = ""):
        """按成交编号查询单笔成交（遍历 query_stock_trades 过滤）。"""
        account = self._resolve_account(account_id)
        trades = self._trader.query_stock_trades(account)
        if trades:
            for t in trades:
                if getattr(t, "traded_id", None) == trade_id:
                    return t
        return None

    def query_single_position(self, stock_code: str, account_id: str = ""):
        """查询单只股票持仓（遍历 query_stock_positions 过滤）。"""
        account = self._resolve_account(account_id)
        positions = self._trader.query_stock_positions(account)
        if positions:
            for p in positions:
                if getattr(p, "stock_code", None) == stock_code:
                    return p
        return None

    # ------------------------------------------------------------------
    # 信用交易操作（融资融券）
    # ------------------------------------------------------------------

    def credit_order(self, stock_code: str, order_type: int, order_volume: int,
                     price_type: int = 5, price: float = 0.0,
                     strategy_name: str = "", order_remark: str = "",
                     account_id: str = ""):
        """信用交易下单（通过 order_type 常量区分融资/融券）→ _trader.order_stock()"""
        account = self._resolve_account(account_id)
        return self._trader.order_stock(
            account, stock_code, order_type, order_volume,
            price_type, price, strategy_name, order_remark,
        )

    def query_credit_positions(self, account_id: str = ""):
        """查询信用账户持仓 → _trader.query_stock_positions()"""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_positions(account)

    def query_credit_detail(self, account_id: str = ""):
        """查询信用账户资产详情 → _trader.query_credit_detail()"""
        account = self._resolve_account(account_id)
        return self._trader.query_credit_detail(account)

    def query_stk_compacts(self, account_id: str = ""):
        """查询信用负债合约 → _trader.query_stk_compacts()"""
        account = self._resolve_account(account_id)
        return self._trader.query_stk_compacts(account)

    def query_credit_slo_code(self, account_id: str = ""):
        """查询融券标的券列表 → _trader.query_credit_slo_code()"""
        account = self._resolve_account(account_id)
        return self._trader.query_credit_slo_code(account)

    def query_credit_subjects(self, account_id: str = ""):
        """查询信用标的券列表 → _trader.query_credit_subjects()"""
        account = self._resolve_account(account_id)
        return self._trader.query_credit_subjects(account)

    def query_credit_assure(self, account_id: str = ""):
        """查询信用担保品信息 → _trader.query_credit_assure()"""
        account = self._resolve_account(account_id)
        return self._trader.query_credit_assure(account)

    # ------------------------------------------------------------------
    # 资金划转
    # ------------------------------------------------------------------

    def fund_transfer(self, transfer_direction: int, amount: float, account_id: str = ""):
        """资金划转 → _trader.fund_transfer()"""
        account = self._resolve_account(account_id)
        return self._trader.fund_transfer(account, transfer_direction, amount)

    # ------------------------------------------------------------------
    # 银证转账（完整实现，对齐 xttrader 真实 API）
    # ------------------------------------------------------------------

    def bank_transfer_in(self, bank_no: str, bank_account: str, balance: float,
                         bank_pwd: str = "", fund_pwd: str = "", account_id: str = ""):
        """银行转证券 → _trader.bank_transfer_in()"""
        account = self._resolve_account(account_id)
        return self._trader.bank_transfer_in(
            account, bank_no, bank_account, balance, bank_pwd, fund_pwd,
        )

    def bank_transfer_out(self, bank_no: str, bank_account: str, balance: float,
                          bank_pwd: str = "", fund_pwd: str = "", account_id: str = ""):
        """证券转银行 → _trader.bank_transfer_out()"""
        account = self._resolve_account(account_id)
        return self._trader.bank_transfer_out(
            account, bank_no, bank_account, balance, bank_pwd, fund_pwd,
        )

    def bank_transfer_in_async(self, bank_no: str, bank_account: str, balance: float,
                               bank_pwd: str = "", fund_pwd: str = "", account_id: str = ""):
        """异步银行转证券 → _trader.bank_transfer_in_async()"""
        account = self._resolve_account(account_id)
        return self._trader.bank_transfer_in_async(
            account, bank_no, bank_account, balance, bank_pwd, fund_pwd,
        )

    def bank_transfer_out_async(self, bank_no: str, bank_account: str, balance: float,
                                bank_pwd: str = "", fund_pwd: str = "", account_id: str = ""):
        """异步证券转银行 → _trader.bank_transfer_out_async()"""
        account = self._resolve_account(account_id)
        return self._trader.bank_transfer_out_async(
            account, bank_no, bank_account, balance, bank_pwd, fund_pwd,
        )

    def query_bank_info(self, account_id: str = ""):
        """查询绑定银行信息 → _trader.query_bank_info()"""
        account = self._resolve_account(account_id)
        return self._trader.query_bank_info(account)

    def query_bank_amount(self, bank_no: str, bank_account: str, bank_pwd: str,
                          account_id: str = ""):
        """查询银行余额 → _trader.query_bank_amount()"""
        account = self._resolve_account(account_id)
        return self._trader.query_bank_amount(account, bank_no, bank_account, bank_pwd)

    def query_bank_transfer_stream(self, start_date: str, end_date: str,
                                   bank_no: str = "", bank_account: str = "",
                                   account_id: str = ""):
        """查询银证转账流水 → _trader.query_bank_transfer_stream()"""
        account = self._resolve_account(account_id)
        return self._trader.query_bank_transfer_stream(
            account, start_date, end_date, bank_no, bank_account,
        )

    # ------------------------------------------------------------------
    # CTP 跨市场资金划转
    # ------------------------------------------------------------------

    def ctp_transfer_option_to_future(self, opt_account_id: str, ft_account_id: str,
                                      balance: float):
        """期权→期货 资金划转 → _trader.ctp_transfer_option_to_future()"""
        return self._trader.ctp_transfer_option_to_future(
            opt_account_id, ft_account_id, balance,
        )

    def ctp_transfer_future_to_option(self, opt_account_id: str, ft_account_id: str,
                                      balance: float):
        """期货→期权 资金划转 → _trader.ctp_transfer_future_to_option()"""
        return self._trader.ctp_transfer_future_to_option(
            opt_account_id, ft_account_id, balance,
        )

    # ------------------------------------------------------------------
    # 证券划转
    # ------------------------------------------------------------------

    def secu_transfer(self, transfer_direction: int, stock_code: str, volume: int,
                      transfer_type: int, account_id: str = ""):
        """证券划转 → _trader.secu_transfer()"""
        account = self._resolve_account(account_id)
        return self._trader.secu_transfer(
            account, transfer_direction, stock_code, volume, transfer_type,
        )

    # ------------------------------------------------------------------
    # SMT 约定式交易操作（完整实现）
    # ------------------------------------------------------------------

    def smt_query_quoter(self, account_id: str = ""):
        """查询 SMT 报价方信息 → _trader.smt_query_quoter()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_query_quoter(account)

    def smt_query_compact(self, account_id: str = ""):
        """查询 SMT 约定合约列表 → _trader.smt_query_compact()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_query_compact(account)

    def smt_query_order(self, account_id: str = ""):
        """查询 SMT 委托 → _trader.smt_query_order()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_query_order(account)

    def smt_negotiate_order_async(self, src_group_id: str, order_code: str,
                                  date: str, amount: float, apply_rate: float,
                                  dict_param: dict | None = None,
                                  account_id: str = ""):
        """异步 SMT 协商下单 → _trader.smt_negotiate_order_async()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_negotiate_order_async(
            account, src_group_id, order_code, date, amount, apply_rate,
            dict_param or {},
        )

    def smt_appointment_order_async(self, order_code: str, date: str,
                                    amount: float, apply_rate: float,
                                    account_id: str = ""):
        """异步 SMT 预约委托 → _trader.smt_appointment_order_async()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_appointment_order_async(
            account, order_code, date, amount, apply_rate,
        )

    def smt_appointment_cancel_async(self, apply_id: str, account_id: str = ""):
        """异步取消 SMT 预约 → _trader.smt_appointment_cancel_async()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_appointment_cancel_async(account, apply_id)

    def smt_compact_renewal_async(self, cash_compact_id: str, order_code: str,
                                  defer_days: int, defer_num: int,
                                  apply_rate: float, account_id: str = ""):
        """异步 SMT 合约展期 → _trader.smt_compact_renewal_async()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_compact_renewal_async(
            account, cash_compact_id, order_code, defer_days, defer_num, apply_rate,
        )

    def smt_compact_return_async(self, src_group_id: str, cash_compact_id: str,
                                 order_code: str, occur_amount: float,
                                 account_id: str = ""):
        """异步 SMT 合约归还 → _trader.smt_compact_return_async()"""
        account = self._resolve_account(account_id)
        return self._trader.smt_compact_return_async(
            account, src_group_id, cash_compact_id, order_code, occur_amount,
        )

    # ------------------------------------------------------------------
    # 新股申购查询
    # ------------------------------------------------------------------

    def query_new_purchase_limit(self, account_id: str = ""):
        """查询新股申购额度 → _trader.query_new_purchase_limit()"""
        account = self._resolve_account(account_id)
        return self._trader.query_new_purchase_limit(account)

    def query_ipo_data(self):
        """查询 IPO 新股日历数据 → _trader.query_ipo_data()"""
        return self._trader.query_ipo_data()

    # ------------------------------------------------------------------
    # 账户信息
    # ------------------------------------------------------------------

    def get_account_status(self, account_id: str = ""):
        """获取账户连接状态（本地判断）。"""
        try:
            return {"connected": self._trader is not None}
        except Exception:
            return {"connected": False}

    def query_account_status(self):
        """查询账户状态 → _trader.query_account_status()"""
        return self._trader.query_account_status()

    def query_secu_account(self, account_id: str = ""):
        """查询证券子账户 → _trader.query_secu_account()"""
        account = self._resolve_account(account_id)
        return self._trader.query_secu_account(account)

    def query_account_infos(self):
        """查询所有已注册账户的信息 → _trader.query_account_infos()"""
        return self._trader.query_account_infos()

    # ------------------------------------------------------------------
    # COM 查询（期权/期货）
    # ------------------------------------------------------------------

    def query_com_fund(self, account_id: str = ""):
        """查询 COM 账户资金 → _trader.query_com_fund()"""
        account = self._resolve_account(account_id)
        return self._trader.query_com_fund(account)

    def query_com_position(self, account_id: str = ""):
        """查询 COM 账户持仓 → _trader.query_com_position()"""
        account = self._resolve_account(account_id)
        return self._trader.query_com_position(account)

    # ------------------------------------------------------------------
    # 数据导出与外部同步（对齐 xttrader 真实签名）
    # ------------------------------------------------------------------

    def export_data(self, result_path: str, data_type: str,
                    start_time: str = "", end_time: str = "",
                    user_param: str = "", account_id: str = ""):
        """导出交易数据 → _trader.export_data()"""
        account = self._resolve_account(account_id)
        return self._trader.export_data(
            account, result_path, data_type, start_time, end_time, user_param,
        )

    def query_data(self, result_path: str, data_type: str,
                   start_time: str = "", end_time: str = "",
                   user_param: str = "", account_id: str = ""):
        """查询导出数据 → _trader.query_data()"""
        account = self._resolve_account(account_id)
        return self._trader.query_data(
            account, result_path, data_type, start_time, end_time, user_param,
        )

    def sync_transaction_from_external(self, operation: str, data_type: str,
                                       deal_list: list, account_id: str = ""):
        """从外部同步交易记录 → _trader.sync_transaction_from_external()"""
        account = self._resolve_account(account_id)
        return self._trader.sync_transaction_from_external(
            operation, data_type, account, deal_list,
        )
