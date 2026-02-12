"""数据下载 — 批量下载、快捷下载。"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _sidebar import require_client

st.set_page_config(page_title="数据下载 - QMT Bridge", layout="wide")
st.title("数据下载")

client = require_client()

# ── 批量下载 ──────────────────────────────────────────────────────

st.header("批量下载")
st.caption("触发服务端下载历史 K 线数据到本地缓存，下载完成后可通过 get_local_data 快速读取。")

col1, col2 = st.columns(2)
with col1:
    dl_stocks = st.text_area(
        "股票代码（每行一个或逗号分隔）",
        value="000001.SZ\n600519.SH",
        height=120,
        key="dl_stocks",
    )
with col2:
    dl_period = st.selectbox("K 线周期", ["1d", "1w", "1m", "5m", "15m", "30m", "60m"], key="dl_period")
    dl_start = st.text_input("开始日期 (YYYYMMDD)", value="", key="dl_start")
    dl_end = st.text_input("结束日期 (YYYYMMDD)", value="", key="dl_end")

if st.button("开始批量下载", key="btn_batch_download", type="primary"):
    codes = [c.strip() for line in dl_stocks.split("\n") for c in line.split(",") if c.strip()]
    if not codes:
        st.warning("请输入至少一个股票代码。")
    else:
        try:
            with st.spinner(f"正在下载 {len(codes)} 只股票的 {dl_period} 数据..."):
                result = client.download_batch(
                    codes,
                    period=dl_period,
                    start_time=dl_start,
                    end_time=dl_end,
                )
            st.success("下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

st.markdown("---")

# ── 快捷下载 ──────────────────────────────────────────────────────

st.header("快捷下载")
st.caption("一键触发服务端下载常用数据集。")

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("下载板块数据", key="btn_dl_sector", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_sector_data()
            st.success("板块数据下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

    if st.button("下载指数权重", key="btn_dl_index", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_index_weight()
            st.success("指数权重下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

    if st.button("下载 ETF 信息", key="btn_dl_etf", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_etf_info()
            st.success("ETF 信息下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

    if st.button("下载节假日数据", key="btn_dl_holiday", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_holiday_data()
            st.success("节假日数据下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

with col2:
    if st.button("下载可转债数据", key="btn_dl_cb", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_cb_data()
            st.success("可转债数据下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

    if st.button("下载历史合约", key="btn_dl_contracts", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_history_contracts()
            st.success("历史合约下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

with col3:
    if st.button("下载合约元数据表", key="btn_dl_metatable", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_metatable_data()
            st.success("合约元数据表下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")

    if st.button("下载表格数据", key="btn_dl_tabular", use_container_width=True):
        try:
            with st.spinner("下载中..."):
                result = client.download_tabular_data([])
            st.success("表格数据下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")


st.markdown("---")

# ── 财务数据下载 ──────────────────────────────────────────────────

st.header("财务数据下载")

fin_stocks = st.text_input(
    "股票代码（逗号分隔）",
    value="000001.SZ, 600519.SH",
    key="fin_dl_stocks",
)
fin_tables = st.multiselect(
    "报表类型",
    ["Balance", "Income", "CashFlow"],
    default=["Balance", "Income", "CashFlow"],
    key="fin_dl_tables",
)

if st.button("下载财务数据", key="btn_dl_financial"):
    codes = [c.strip() for c in fin_stocks.split(",") if c.strip()]
    if not codes:
        st.warning("请输入至少一个股票代码。")
    else:
        try:
            with st.spinner("下载中..."):
                result = client.download_financial_data2(codes, tables=fin_tables)
            st.success("财务数据下载完成")
            st.json(result)
        except Exception as e:
            st.error(f"下载失败: {e}")
