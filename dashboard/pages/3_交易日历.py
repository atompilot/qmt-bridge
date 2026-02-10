"""交易日历 — 交易日查询、日期校验、节假日。"""

import sys
from pathlib import Path
from datetime import date

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _sidebar import require_client

st.set_page_config(page_title="交易日历 - QMT Bridge", layout="wide")
st.title("交易日历")

client = require_client()

# ── 交易日查询 ────────────────────────────────────────────────────

st.header("交易日查询")

col1, col2, col3 = st.columns(3)
with col1:
    market = st.selectbox("市场", ["SH", "SZ", "BJ"], key="td_market")
with col2:
    start_date = st.date_input("开始日期", value=date(date.today().year, 1, 1), key="td_start")
with col3:
    end_date = st.date_input("结束日期", value=date.today(), key="td_end")

if st.button("查询交易日", key="btn_trading_dates"):
    try:
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        with st.spinner("查询中..."):
            dates = client.get_trading_dates(market, start_time=start_str, end_time=end_str)
        if not dates:
            st.info("未获取到交易日数据。")
        else:
            st.success(f"共 {len(dates)} 个交易日")
            df = pd.DataFrame({"交易日": dates})
            st.dataframe(df, use_container_width=True, height=300)
    except Exception as e:
        st.error(f"查询失败: {e}")

st.markdown("---")

# ── 日期校验 ──────────────────────────────────────────────────────

st.header("日期校验")

col1, col2 = st.columns(2)
with col1:
    check_market = st.selectbox("市场", ["SH", "SZ", "BJ"], key="check_market")
with col2:
    check_date = st.date_input("待检查日期", value=date.today(), key="check_date")

if st.button("校验是否交易日", key="btn_is_trading"):
    try:
        date_str = check_date.strftime("%Y%m%d")
        result = client.is_trading_date(check_market, date_str)
        if result:
            st.success(f"{check_date} 是交易日")
        else:
            st.warning(f"{check_date} 不是交易日")
    except Exception as e:
        st.error(f"校验失败: {e}")

col1, col2 = st.columns(2)
with col1:
    if st.button("查询上一个交易日", key="btn_prev_td"):
        try:
            date_str = check_date.strftime("%Y%m%d")
            prev = client.get_prev_trading_date(check_market, date_str)
            st.info(f"上一个交易日: {prev}")
        except Exception as e:
            st.error(f"查询失败: {e}")

with col2:
    if st.button("查询下一个交易日", key="btn_next_td"):
        try:
            date_str = check_date.strftime("%Y%m%d")
            nxt = client.get_next_trading_date(check_market, date_str)
            st.info(f"下一个交易日: {nxt}")
        except Exception as e:
            st.error(f"查询失败: {e}")

st.markdown("---")

# ── 节假日 ────────────────────────────────────────────────────────

st.header("节假日")

if st.button("获取节假日列表", key="btn_holidays"):
    try:
        with st.spinner("查询中..."):
            holidays = client.get_holidays()
        if not holidays:
            st.info("未获取到节假日数据。")
        else:
            st.success(f"共 {len(holidays)} 个节假日")
            df = pd.DataFrame({"节假日": holidays})
            st.dataframe(df, use_container_width=True, height=300)
    except Exception as e:
        st.error(f"查询失败: {e}")
