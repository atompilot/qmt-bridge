"""行情数据 — K 线图、实时快照、大盘指数。"""

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
import pandas as pd

# 将 dashboard/ 加入 sys.path 以便 import _sidebar
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _sidebar import require_client

st.set_page_config(page_title="行情数据 - QMT Bridge", layout="wide")
st.title("行情数据")

client = require_client()

# ── K 线图 ────────────────────────────────────────────────────────

st.header("K 线图")

col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
with col1:
    stock_code = st.text_input("股票代码", value="000001.SZ", key="kline_stock")
with col2:
    period = st.selectbox("周期", ["1d", "1w", "1m", "5m", "15m", "30m", "60m"], key="kline_period")
with col3:
    count = st.number_input("条数", value=120, min_value=10, max_value=1000, step=10, key="kline_count")
with col4:
    dividend_type = st.selectbox(
        "除权类型",
        ["none", "front", "back", "front_ratio", "back_ratio"],
        format_func=lambda x: {
            "none": "不复权",
            "front": "前复权",
            "back": "后复权",
            "front_ratio": "等比前复权",
            "back_ratio": "等比后复权",
        }.get(x, x),
        key="kline_dividend",
    )

if st.button("查询 K 线", key="btn_kline"):
    try:
        with st.spinner("查询中..."):
            data = client.get_history_ex(
                [stock_code],
                period=period,
                count=count,
                dividend_type=dividend_type,
            )
        df = data.get(stock_code)
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            st.info("未获取到数据。")
        else:
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)

            x_axis = df["time"] if "time" in df.columns else df.index

            fig = go.Figure(data=[go.Candlestick(
                x=x_axis,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
            )])
            fig.update_layout(
                title=f"{stock_code} — {period} K 线",
                xaxis_title="日期",
                yaxis_title="价格",
                xaxis_rangeslider_visible=False,
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)

            if "volume" in df.columns:
                vol_fig = go.Figure(data=[go.Bar(
                    x=x_axis,
                    y=df["volume"],
                    marker_color="steelblue",
                )])
                vol_fig.update_layout(title="成交量", height=200, xaxis_rangeslider_visible=False)
                st.plotly_chart(vol_fig, use_container_width=True)

            with st.expander("查看原始数据"):
                st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"查询失败: {e}")

st.markdown("---")

# ── 实时快照 ──────────────────────────────────────────────────────

st.header("实时快照")

snapshot_codes = st.text_input(
    "输入股票代码（逗号分隔）",
    value="000001.SZ, 600519.SH, 000858.SZ",
    key="snapshot_codes",
)

if st.button("获取快照", key="btn_snapshot"):
    try:
        codes = [c.strip() for c in snapshot_codes.split(",") if c.strip()]
        with st.spinner("查询中..."):
            data = client.get_market_snapshot(codes)
        if not data:
            st.info("未获取到数据。")
        else:
            rows = []
            for code, info in data.items():
                if isinstance(info, dict):
                    rows.append({**info, "代码": code})
            if rows:
                df = pd.DataFrame(rows)
                if "代码" in df.columns:
                    cols = ["代码"] + [c for c in df.columns if c != "代码"]
                    df = df[cols]
                st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.error(f"查询失败: {e}")

st.markdown("---")

# ── 大盘指数 ──────────────────────────────────────────────────────

st.header("大盘指数")

if st.button("刷新指数", key="btn_indices"):
    try:
        with st.spinner("查询中..."):
            data = client.get_major_indices()
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if not data:
            st.info("未获取到指数数据。")
        else:
            if isinstance(data, dict):
                rows = []
                for code, info in data.items():
                    if isinstance(info, dict):
                        rows.append({**info, "代码": code})
                if rows:
                    df = pd.DataFrame(rows)
                    if "代码" in df.columns:
                        cols = ["代码"] + [c for c in df.columns if c != "代码"]
                        df = df[cols]
                    st.dataframe(df, use_container_width=True)
                else:
                    st.json(data)
            elif isinstance(data, list):
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.json(data)
    except Exception as e:
        st.error(f"查询失败: {e}")
