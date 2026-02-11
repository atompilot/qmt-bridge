"""XtTraderManager — lifecycle management for XtQuantTrader."""

import logging

logger = logging.getLogger("qmt_bridge.trading")


class XtTraderManager:
    """Manages an XtQuantTrader instance.

    Created during FastAPI lifespan startup when trading is enabled.
    """

    def __init__(self, mini_qmt_path: str = "", account_id: str = ""):
        self.mini_qmt_path = mini_qmt_path
        self.account_id = account_id
        self._trader = None
        self._account = None

    def connect(self):
        """Initialize and connect the XtQuantTrader instance."""
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
        """Disconnect and clean up."""
        if self._trader is not None:
            try:
                self._trader.stop()
            except Exception:
                logger.exception("Error stopping XtQuantTrader")
            self._trader = None

    def _resolve_account(self, account_id: str = ""):
        """Get the StockAccount — use provided or default."""
        if account_id and account_id != self.account_id:
            from xtquant.xttype import StockAccount
            return StockAccount(account_id)
        return self._account

    # ------------------------------------------------------------------
    # Order operations
    # ------------------------------------------------------------------

    def order(self, stock_code: str, order_type: int, order_volume: int,
              price_type: int = 5, price: float = 0.0,
              strategy_name: str = "", order_remark: str = "",
              account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.order_stock(
            account, stock_code, order_type, order_volume,
            price_type, price, strategy_name, order_remark,
        )

    def cancel_order(self, order_id: int, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.cancel_order_stock(account, order_id)

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------

    def query_orders(self, account_id: str = "", cancelable_only: bool = False):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_orders(account, cancelable_only)

    def query_positions(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_positions(account)

    def query_asset(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_asset(account)

    def query_trades(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_trades(account)

    def query_order_detail(self, order_id: int = 0, account_id: str = ""):
        account = self._resolve_account(account_id)
        orders = self._trader.query_stock_orders(account, False)
        if orders:
            for o in orders:
                if getattr(o, "order_id", None) == order_id:
                    return o
        return None

    # ------------------------------------------------------------------
    # Credit operations
    # ------------------------------------------------------------------

    def credit_order(self, stock_code: str, order_type: int, order_volume: int,
                     price_type: int = 5, price: float = 0.0,
                     credit_type: str = "fin_buy",
                     strategy_name: str = "", order_remark: str = "",
                     account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.order_stock(
            account, stock_code, order_type, order_volume,
            price_type, price, strategy_name, order_remark,
        )

    def query_credit_positions(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_positions(account)

    def query_credit_asset(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_asset(account)

    def query_credit_debt(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_credit_debt(account)

    def query_credit_available(self, stock_code: str = "", account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_credit_available(account, stock_code)

    def query_slo_stocks(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_slo_stocks(account)

    def query_fin_stocks(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_fin_stocks(account)

    # ------------------------------------------------------------------
    # Fund operations
    # ------------------------------------------------------------------

    def fund_transfer(self, transfer_direction: int, amount: float, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.fund_transfer(account, transfer_direction, amount)

    def query_fund_transfer_records(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_fund_transfer(account)

    def query_available_fund(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        asset = self._trader.query_stock_asset(account)
        return asset

    def ctp_fund_transfer(self, direction: int, amount: float, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.fund_transfer(account, direction, amount)

    def query_ctp_balance(self, account_id: str = ""):
        return self.query_available_fund(account_id)

    # ------------------------------------------------------------------
    # Bank operations
    # ------------------------------------------------------------------

    def bank_transfer(self, direction: int, amount: float, bank_code: str = "", account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.fund_transfer(account, direction, amount)

    def query_bank_balance(self, account_id: str = ""):
        return self.query_available_fund(account_id)

    def query_bank_transfer_records(self, account_id: str = ""):
        return self.query_fund_transfer_records(account_id)

    def query_bound_banks(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_asset(account)

    def query_transfer_limit(self, account_id: str = ""):
        return self.query_available_fund(account_id)

    def query_bank_available(self, account_id: str = ""):
        return self.query_available_fund(account_id)

    def query_bank_transfer_status(self, transfer_id: str = "", account_id: str = ""):
        return self.query_fund_transfer_records(account_id)

    # ------------------------------------------------------------------
    # SMT operations (约定式交易 — real API)
    # ------------------------------------------------------------------

    def smt_order(self, stock_code: str, order_type: int, order_volume: int,
                  price_type: int = 5, price: float = 0.0,
                  smt_type: str = "", strategy_name: str = "", order_remark: str = "",
                  account_id: str = ""):
        """Place an SMT order using order_stock with SMT-specific parameters."""
        account = self._resolve_account(account_id)
        return self._trader.order_stock(
            account, stock_code, order_type, order_volume,
            price_type, price, strategy_name, order_remark,
        )

    def smt_negotiate_order_async(self, stock_code: str, order_type: int,
                                  order_volume: int, price: float = 0.0,
                                  compact_id: str = "",
                                  strategy_name: str = "", order_remark: str = "",
                                  account_id: str = ""):
        """Async SMT negotiate order — result via on_smt_appointment_async_response callback."""
        account = self._resolve_account(account_id)
        return self._trader.smt_negotiate_order_async(
            account, stock_code, order_type, order_volume,
            price, compact_id, strategy_name, order_remark,
        )

    def cancel_smt_order(self, order_id: int, account_id: str = ""):
        """Cancel an SMT order."""
        account = self._resolve_account(account_id)
        return self._trader.cancel_order_stock(account, order_id)

    def smt_query_quoter(self, account_id: str = ""):
        """Query SMT quoter information (报价方信息)."""
        account = self._resolve_account(account_id)
        return self._trader.smt_query_quoter(account)

    def smt_query_compact(self, account_id: str = ""):
        """Query SMT compacts (约定合约)."""
        account = self._resolve_account(account_id)
        return self._trader.smt_query_compact(account)

    def query_appointment_info(self, account_id: str = ""):
        """Query SMT appointment info (约定式预约信息)."""
        account = self._resolve_account(account_id)
        return self._trader.query_appointment_info(account)

    def query_smt_secu_info(self, account_id: str = ""):
        """Query SMT security info (约定式证券信息)."""
        account = self._resolve_account(account_id)
        return self._trader.query_smt_secu_info(account)

    def query_smt_secu_rate(self, account_id: str = ""):
        """Query SMT security rates (约定式证券费率)."""
        account = self._resolve_account(account_id)
        return self._trader.query_smt_secu_rate(account)

    # ------------------------------------------------------------------
    # Async order operations
    # ------------------------------------------------------------------

    def order_async(self, stock_code: str, order_type: int, order_volume: int,
                    price_type: int = 5, price: float = 0.0,
                    strategy_name: str = "", order_remark: str = "",
                    account_id: str = ""):
        """Async order — result delivered via on_order_stock_async_response callback."""
        account = self._resolve_account(account_id)
        return self._trader.order_stock_async(
            account, stock_code, order_type, order_volume,
            price_type, price, strategy_name, order_remark,
        )

    def cancel_order_async(self, order_id: int, account_id: str = ""):
        """Async cancel — result delivered via on_cancel_order_stock_async_response callback."""
        account = self._resolve_account(account_id)
        return self._trader.cancel_order_stock_async(account, order_id)

    # ------------------------------------------------------------------
    # Single-item queries
    # ------------------------------------------------------------------

    def query_single_order(self, order_id: int, account_id: str = ""):
        """Query a single order by order_id."""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_order(account, order_id)

    def query_single_trade(self, trade_id: int, account_id: str = ""):
        """Query a single trade by trade_id."""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_trade(account, trade_id)

    def query_single_position(self, stock_code: str, account_id: str = ""):
        """Query position for a single stock."""
        account = self._resolve_account(account_id)
        return self._trader.query_stock_position(account, stock_code)

    # ------------------------------------------------------------------
    # Position statistics
    # ------------------------------------------------------------------

    def query_position_statistics(self, account_id: str = ""):
        """Query position statistics summary."""
        account = self._resolve_account(account_id)
        return self._trader.query_position_statistics(account)

    # ------------------------------------------------------------------
    # Credit extended queries
    # ------------------------------------------------------------------

    def query_credit_subjects(self, account_id: str = ""):
        """Query credit subject list."""
        account = self._resolve_account(account_id)
        return self._trader.query_credit_subjects(account)

    def query_credit_assure(self, account_id: str = ""):
        """Query credit assurance / collateral info."""
        account = self._resolve_account(account_id)
        return self._trader.query_credit_assure(account)

    # ------------------------------------------------------------------
    # IPO queries
    # ------------------------------------------------------------------

    def query_new_purchase_limit(self, account_id: str = ""):
        """Query IPO new purchase limit."""
        account = self._resolve_account(account_id)
        return self._trader.query_new_purchase_limit(account)

    def query_ipo_data(self):
        """Query IPO calendar data."""
        return self._trader.query_ipo_data()

    # ------------------------------------------------------------------
    # Account info
    # ------------------------------------------------------------------

    def get_account_status(self, account_id: str = ""):
        try:
            return {"connected": self._trader is not None}
        except Exception:
            return {"connected": False}

    def get_account_info(self, account_id: str = ""):
        account = self._resolve_account(account_id)
        return self._trader.query_stock_asset(account)

    def query_account_infos(self):
        """Query info for all registered accounts."""
        return self._trader.query_account_infos()

    # ------------------------------------------------------------------
    # COM queries
    # ------------------------------------------------------------------

    def query_com_fund(self, account_id: str = ""):
        """Query COM fund (期权/期货账户资金)."""
        account = self._resolve_account(account_id)
        return self._trader.query_com_fund(account)

    def query_com_position(self, account_id: str = ""):
        """Query COM positions (期权/期货持仓)."""
        account = self._resolve_account(account_id)
        return self._trader.query_com_position(account)

    # ------------------------------------------------------------------
    # CTP cross-market transfers
    # ------------------------------------------------------------------

    def ctp_transfer_option_to_future(self, amount: float, account_id: str = ""):
        """Transfer from option account to future account."""
        account = self._resolve_account(account_id)
        return self._trader.ctp_transfer_option_to_future(account, amount)

    def ctp_transfer_future_to_option(self, amount: float, account_id: str = ""):
        """Transfer from future account to option account."""
        account = self._resolve_account(account_id)
        return self._trader.ctp_transfer_future_to_option(account, amount)

    # ------------------------------------------------------------------
    # Data export / external sync
    # ------------------------------------------------------------------

    def export_data(self, data_type: str = "orders", file_path: str = "", account_id: str = ""):
        """Export trading data to file."""
        account = self._resolve_account(account_id)
        return self._trader.export_data(account, data_type, file_path)

    def query_data(self, data_type: str = "orders", account_id: str = ""):
        """Query exported trading data."""
        account = self._resolve_account(account_id)
        return self._trader.query_data(account, data_type)

    def sync_transaction_from_external(self, data: list, account_id: str = ""):
        """Sync external transaction records into the system."""
        account = self._resolve_account(account_id)
        return self._trader.sync_transaction_from_external(account, data)
