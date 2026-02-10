"""板块管理 — 板块列表、成分股查询。"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _sidebar import require_client

st.set_page_config(page_title="板块管理 - QMT Bridge", layout="wide")
st.title("板块管理")

client = require_client()

# ── 板块列表 ──────────────────────────────────────────────────────

st.header("板块列表")

if st.button("加载板块列表", key="btn_sector_list"):
    try:
        with st.spinner("加载中..."):
            sectors = client.get_sector_list()
        if not sectors:
            st.info("未获取到板块数据。")
        else:
            st.session_state["sectors"] = sectors
            st.success(f"共 {len(sectors)} 个板块")
    except Exception as e:
        st.error(f"获取板块列表失败: {e}")

sectors = st.session_state.get("sectors", [])
if sectors:
    selected = st.selectbox("选择板块", sectors, key="sector_select")
else:
    selected = st.text_input("输入板块名称", key="sector_input")

st.markdown("---")

# ── 成分股 ────────────────────────────────────────────────────────

st.header("成分股")

if st.button("查询成分股", key="btn_sector_stocks"):
    sector_name = selected if selected else ""
    if not sector_name:
        st.warning("请先选择或输入板块名称。")
    else:
        try:
            with st.spinner("查询中..."):
                stocks = client.get_sector_stocks(sector_name)
            if not stocks:
                st.info(f"板块「{sector_name}」无成分股数据。")
            else:
                st.success(f"板块「{sector_name}」共 {len(stocks)} 只成分股")
                try:
                    names = client.get_batch_stock_name(stocks[:100])
                    rows = [{"代码": s, "名称": names.get(s, "")} for s in stocks]
                except Exception:
                    rows = [{"代码": s} for s in stocks]
                df = pd.DataFrame(rows)
                st.dataframe(df, use_container_width=True, height=400)
        except Exception as e:
            st.error(f"查询成分股失败: {e}")

st.markdown("---")

# ── 板块详情 ──────────────────────────────────────────────────────

st.header("板块详情")

sector_info_name = st.text_input("板块名称（留空查全部）", key="sector_info_input")

if st.button("查询板块信息", key="btn_sector_info"):
    try:
        with st.spinner("查询中..."):
            info = client.get_sector_info(sector_info_name)
        if not info:
            st.info("未获取到板块信息。")
        else:
            st.json(info)
    except Exception as e:
        st.error(f"查询板块信息失败: {e}")
