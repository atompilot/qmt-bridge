"""合约信息 — 合约详情、指数权重、期权链、ETF/可转债。"""

import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from _sidebar import require_client

st.set_page_config(page_title="合约信息 - QMT Bridge", layout="wide")
st.title("合约信息")

client = require_client()

tab1, tab2, tab3, tab4 = st.tabs(["合约详情", "指数权重", "期权链", "ETF / 可转债"])

# ── 合约详情 ──────────────────────────────────────────────────────

with tab1:
    st.header("合约详情")
    codes_input = st.text_input(
        "输入合约代码（逗号分隔）",
        value="000001.SZ, 600519.SH",
        key="inst_codes",
    )
    iscomplete = st.checkbox("完整信息", value=False, key="inst_complete")

    if st.button("查询合约", key="btn_instrument"):
        try:
            codes = [c.strip() for c in codes_input.split(",") if c.strip()]
            with st.spinner("查询中..."):
                data = client.get_batch_instrument_detail(codes, iscomplete=iscomplete)
            if not data:
                st.info("未获取到合约信息。")
            else:
                if isinstance(data, dict):
                    for code, detail in data.items():
                        with st.expander(f"{code}", expanded=True):
                            if isinstance(detail, dict):
                                st.json(detail)
                            else:
                                st.write(detail)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询失败: {e}")

# ── 指数权重 ──────────────────────────────────────────────────────

with tab2:
    st.header("指数权重")
    index_code = st.text_input("指数代码", value="000300.SH", key="idx_code")

    if st.button("查询权重", key="btn_index_weight"):
        try:
            with st.spinner("查询中..."):
                data = client.get_index_weight(index_code)
            if not data:
                st.info("未获取到权重数据。")
            else:
                if isinstance(data, dict):
                    rows = [{"成分股": k, "权重": v} for k, v in data.items()]
                    df = pd.DataFrame(rows)
                    df = df.sort_values("权重", ascending=False)
                    st.success(f"共 {len(df)} 只成分股")
                    st.dataframe(df, use_container_width=True, height=400)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询失败: {e}")

# ── 期权链 ────────────────────────────────────────────────────────

with tab3:
    st.header("期权链")
    undl_code = st.text_input("标的代码", value="510050.SH", key="opt_undl")

    if st.button("查询期权链", key="btn_option_chain"):
        try:
            with st.spinner("查询中..."):
                data = client.get_option_chain(undl_code)
            if not data:
                st.info("未获取到期权链数据。")
            else:
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, height=400)
                elif isinstance(data, dict):
                    for expiry, options in data.items():
                        with st.expander(f"到期日: {expiry}", expanded=True):
                            if isinstance(options, list):
                                st.dataframe(pd.DataFrame(options), use_container_width=True)
                            else:
                                st.json(options)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询失败: {e}")

    st.subheader("期权列表")
    col1, col2, col3 = st.columns(3)
    with col1:
        opt_undl2 = st.text_input("标的代码", value="510050.SH", key="opt_undl2")
    with col2:
        opt_dedate = st.text_input("到期月份 (YYYYMM)", value="", key="opt_dedate")
    with col3:
        opt_type = st.selectbox("期权类型", ["", "CALL", "PUT"], key="opt_type")

    if st.button("查询期权列表", key="btn_option_list"):
        if not opt_dedate:
            st.warning("请输入到期月份。")
        else:
            try:
                with st.spinner("查询中..."):
                    data = client.get_option_list(opt_undl2, opt_dedate, opttype=opt_type)
                if not data:
                    st.info("未获取到期权列表。")
                else:
                    if isinstance(data, list):
                        df = pd.DataFrame({"期权代码": data})
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.json(data)
            except Exception as e:
                st.error(f"查询失败: {e}")

# ── ETF / 可转债 ──────────────────────────────────────────────────

with tab4:
    st.header("ETF / 可转债")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("ETF 列表")
        if st.button("获取 ETF 列表", key="btn_etf_list"):
            try:
                with st.spinner("查询中..."):
                    etfs = client.get_etf_list()
                if not etfs:
                    st.info("未获取到 ETF 数据。")
                else:
                    st.success(f"共 {len(etfs)} 只 ETF")
                    df = pd.DataFrame({"ETF 代码": etfs})
                    st.dataframe(df, use_container_width=True, height=300)
            except Exception as e:
                st.error(f"查询失败: {e}")

    with col2:
        st.subheader("可转债列表")
        if st.button("获取可转债列表", key="btn_cb_list"):
            try:
                with st.spinner("查询中..."):
                    cbs = client.get_cb_list()
                if not cbs:
                    st.info("未获取到可转债数据。")
                else:
                    st.success(f"共 {len(cbs)} 只可转债")
                    df = pd.DataFrame({"可转债代码": cbs})
                    st.dataframe(df, use_container_width=True, height=300)
            except Exception as e:
                st.error(f"查询失败: {e}")

    st.markdown("---")

    st.subheader("ETF 申赎信息")
    if st.button("获取 ETF 申赎信息", key="btn_etf_info"):
        try:
            with st.spinner("查询中..."):
                data = client.get_etf_info()
            if not data:
                st.info("未获取到 ETF 申赎信息。")
            else:
                if isinstance(data, list):
                    st.dataframe(pd.DataFrame(data), use_container_width=True)
                else:
                    st.json(data)
        except Exception as e:
            st.error(f"查询失败: {e}")

    st.subheader("可转债详情")
    cb_code = st.text_input("可转债代码", key="cb_detail_code")
    if st.button("查询可转债详情", key="btn_cb_detail"):
        if not cb_code:
            st.warning("请输入可转债代码。")
        else:
            try:
                with st.spinner("查询中..."):
                    data = client.get_cb_info(cb_code)
                if not data:
                    st.info("未获取到可转债详情。")
                else:
                    st.json(data)
            except Exception as e:
                st.error(f"查询失败: {e}")
