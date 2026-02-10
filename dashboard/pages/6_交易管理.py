"""交易管理 — 下单、撤单、持仓、资产、成交（需要 API Key）。"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _sidebar import require_client

st.set_page_config(page_title="交易管理 - QMT Bridge", layout="wide")
st.title("交易管理")

client = require_client()

if not getattr(client, "api_key", ""):
    st.warning("交易功能需要 API Key，请在侧边栏输入后重新连接。")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["下单", "当日委托", "持仓", "资产", "成交记录"])

# ── 下单 ──────────────────────────────────────────────────────────

with tab1:
    st.header("委托下单")
    st.caption("请谨慎操作，下单将直接提交到交易系统。")

    col1, col2 = st.columns(2)
    with col1:
        order_stock = st.text_input("股票代码", value="", key="order_stock")
        order_type = st.selectbox(
            "买卖方向",
            [23, 24],
            format_func=lambda x: "买入" if x == 23 else "卖出",
            key="order_type",
        )
        order_volume = st.number_input("委托数量（股）", value=100, min_value=1, step=100, key="order_vol")
    with col2:
        price_type = st.selectbox(
            "报价类型",
            [5, 11],
            format_func=lambda x: {5: "最新价", 11: "限价"}.get(x, str(x)),
            key="price_type",
        )
        price = st.number_input("委托价格（限价时填写）", value=0.0, step=0.01, key="order_price")
        order_remark = st.text_input("备注（可选）", value="", key="order_remark")

    # 两步确认：先勾选确认框，再点击提交
    order_confirm = st.checkbox("我确认提交此委托", value=False, key="order_confirm")

    if st.button("提交委托", key="btn_order", type="primary"):
        if not order_stock:
            st.warning("请输入股票代码。")
        elif not order_confirm:
            direction = "买入" if order_type == 23 else "卖出"
            st.warning(f"即将 **{direction} {order_stock}**，数量 **{order_volume}** 股。请先勾选确认框。")
        else:
            try:
                with st.spinner("提交中..."):
                    result = client.place_order(
                        stock_code=order_stock,
                        order_type=order_type,
                        order_volume=order_volume,
                        price_type=price_type,
                        price=price,
                        order_remark=order_remark,
                    )
                st.success("委托已提交")
                st.json(result)
            except Exception as e:
                st.error(f"下单失败: {e}")

# ── 当日委托 ──────────────────────────────────────────────────────

with tab2:
    st.header("当日委托")

    cancelable_only = st.checkbox("仅显示可撤委托", value=False, key="cancelable_only")

    if st.button("刷新委托列表", key="btn_orders"):
        try:
            with st.spinner("查询中..."):
                data = client.query_orders(cancelable_only=cancelable_only)
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not data:
                st.info("暂无委托数据。")
            else:
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询委托失败: {e}")

    st.subheader("撤单")
    cancel_id = st.number_input("委托 ID", value=0, min_value=0, step=1, key="cancel_id")
    if st.button("撤销委托", key="btn_cancel"):
        if cancel_id <= 0:
            st.warning("请输入有效的委托 ID。")
        else:
            try:
                with st.spinner("撤单中..."):
                    result = client.cancel_order(cancel_id)
                st.success("撤单请求已提交")
                st.json(result)
            except Exception as e:
                st.error(f"撤单失败: {e}")

# ── 持仓 ──────────────────────────────────────────────────────────

with tab3:
    st.header("持仓")

    if st.button("刷新持仓", key="btn_positions"):
        try:
            with st.spinner("查询中..."):
                data = client.query_positions()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not data:
                st.info("暂无持仓数据。")
            else:
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询持仓失败: {e}")

# ── 资产 ──────────────────────────────────────────────────────────

with tab4:
    st.header("资产概览")

    if st.button("刷新资产", key="btn_asset"):
        try:
            with st.spinner("查询中..."):
                data = client.query_asset()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not data:
                st.info("暂无资产数据。")
            else:
                if isinstance(data, dict):
                    cols = st.columns(4)
                    keys = list(data.keys())
                    for i, key in enumerate(keys[:8]):
                        with cols[i % 4]:
                            st.metric(key, data[key])
                    if len(keys) > 8:
                        with st.expander("全部字段"):
                            st.json(data)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询资产失败: {e}")

# ── 成交记录 ──────────────────────────────────────────────────────

with tab5:
    st.header("成交记录")

    if st.button("刷新成交记录", key="btn_trades"):
        try:
            with st.spinner("查询中..."):
                data = client.query_trades()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not data:
                st.info("暂无成交数据。")
            else:
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询成交失败: {e}")
