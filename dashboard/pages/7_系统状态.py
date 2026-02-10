"""系统状态 — 健康检查、版本信息、连接状态、可用市场/周期。"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _sidebar import require_client

st.set_page_config(page_title="系统状态 - QMT Bridge", layout="wide")
st.title("系统状态")

client = require_client()

# ── 健康检查 & 版本 ───────────────────────────────────────────────

st.header("健康检查")

if st.button("运行健康检查", key="btn_health"):
    try:
        health = client.health_check()
        st.success("服务正常")
        st.json(health)
    except Exception as e:
        st.error(f"健康检查失败: {e}")

st.markdown("---")

st.header("版本信息")

col1, col2 = st.columns(2)
with col1:
    try:
        version = client.get_server_version()
        st.metric("QMT Bridge 服务端版本", version)
    except Exception as e:
        st.error(f"获取服务端版本失败: {e}")

with col2:
    try:
        xtdata_ver = client.get_xtdata_version()
        st.metric("xtquant / xtdata 版本", xtdata_ver)
    except Exception as e:
        st.error(f"获取 xtdata 版本失败: {e}")

st.markdown("---")

# ── 连接状态 ──────────────────────────────────────────────────────

st.header("连接状态")

if st.button("刷新连接状态", key="btn_conn_status"):
    try:
        status = client.get_connection_status()
        st.json(status)
    except Exception as e:
        st.error(f"获取连接状态失败: {e}")

if st.button("行情服务器状态", key="btn_quote_status"):
    try:
        status = client.get_quote_server_status()
        st.json(status)
    except Exception as e:
        st.error(f"获取行情服务器状态失败: {e}")

st.markdown("---")

# ── 可用市场 ──────────────────────────────────────────────────────

st.header("可用市场")

if st.button("获取可用市场", key="btn_markets"):
    try:
        with st.spinner("查询中..."):
            data = client.get_markets()
        if isinstance(data, dict) and "data" in data:
            data = data["data"]
        if not data:
            st.info("未获取到市场数据。")
        else:
            if isinstance(data, dict):
                rows = [{"市场代码": k, "说明": v} for k, v in data.items()]
                st.dataframe(pd.DataFrame(rows), use_container_width=True)
            elif isinstance(data, list):
                st.dataframe(pd.DataFrame({"市场": data}), use_container_width=True)
            else:
                st.json(data)
    except Exception as e:
        st.error(f"获取市场列表失败: {e}")

st.markdown("---")

# ── 可用周期 ──────────────────────────────────────────────────────

st.header("可用 K 线周期")

if st.button("获取可用周期", key="btn_periods"):
    try:
        with st.spinner("查询中..."):
            periods = client.get_periods()
        if not periods:
            st.info("未获取到周期数据。")
        else:
            if isinstance(periods, list):
                st.dataframe(pd.DataFrame({"周期": periods}), use_container_width=True)
            else:
                st.json(periods)
    except Exception as e:
        st.error(f"获取周期列表失败: {e}")

st.markdown("---")

# ── 最后交易日 ────────────────────────────────────────────────────

st.header("最后交易日")

ltd_market = st.selectbox("市场", ["SH", "SZ", "BJ"], key="ltd_market")

if st.button("查询最后交易日", key="btn_last_trade_date"):
    try:
        last_date = client.get_last_trade_date(ltd_market)
        st.info(f"市场 {ltd_market} 最后交易日: **{last_date}**")
    except Exception as e:
        st.error(f"查询失败: {e}")
