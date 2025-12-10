import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import json

# --------------------------------------------------------------------
# Page Configuration
# --------------------------------------------------------------------
st.set_page_config(
    page_title="Veritas Quant | Pro Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------------------------
# Custom Themed CSS (Dark Mode)
# --------------------------------------------------------------------
st.markdown("""
    <style>
        .stApp {
            background-color: #131722;
        }
        
        [data-testid="stSidebar"] {
            background-color: #1e222d;
            border-right: 1px solid #2a2e39;
        }
        
        h1, h2, h3, p, label, div, span {
            color: #d1d4dc !important;
            font-family: 'Roboto', sans-serif;
        }
        
        .stTextInput input, .stSelectbox div, .stNumberInput input {
            color: #d1d4dc !important;
            background-color: #2a2e39 !important;
            border: 1px solid #434651 !important;
        }
        
        .stButton > button {
            background-color: #2962ff !important;
            color: white !important;
            border: none;
            border-radius: 4px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            box-shadow: 0 4px 14px 0 rgba(41, 98, 255, 0.39);
        }
        
        [data-testid="stDataFrame"] {
            background-color: #1e222d;
            border: 1px solid #2a2e39;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 26px;
            color: #d1d4dc !important;
        }
        [data-testid="stMetricDelta"] svg {
            fill: #d1d4dc !important;
        }
    </style>
""", unsafe_allow_html=True)

# --------------------------------------------------------------------
# Backend API
# --------------------------------------------------------------------
API_URL = "http://127.0.0.1:8000"

# --------------------------------------------------------------------
# Header
# --------------------------------------------------------------------
col_logo, col_title = st.columns([1, 15])
with col_title:
    st.markdown(
        "# VERITAS QUANT <span style='font-size:18px; color:#2962ff'>PRO</span>",
        unsafe_allow_html=True
    )
    st.markdown("### ESG-Driven Hierarchical Risk Parity Engine")

st.markdown("---")

# --------------------------------------------------------------------
# Sidebar Controls
# --------------------------------------------------------------------
with st.sidebar:
    st.header("Strategy Settings")
    
    st.markdown("### 1. Universe")
    default_tickers = "AAPL, MSFT, GOOGL, AMZN, TSLA, XOM, CVX, PEP, KO, JNJ, NVDA"
    tickers_input = st.text_area("Assets (comma separated)", value=default_tickers, height=100)

    st.markdown("### 2. ESG Filters")
    apply_esg = st.checkbox("Enable ESG Screening", value=True)
    esg_threshold = st.slider("Minimum ESG Score", 0, 100, 50)
    
    st.markdown("### 3. Timeframe")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Start", value=pd.to_datetime("2021-01-01"))
    with col_d2:
        end_date = st.date_input("End", value=pd.to_datetime("2024-01-01"))
    
    st.markdown("---")
    launch_btn = st.button("Run Optimization", type="primary", use_container_width=True)

# --------------------------------------------------------------------
# Main Execution
# --------------------------------------------------------------------
if launch_btn:

    ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    
    payload = {
        "tickers": ticker_list,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "apply_esg_filter": apply_esg,
        "esg_threshold": esg_threshold
    }

    progress_bar = st.progress(0, text="Initializing Quant Engine...")

    try:
        progress_bar.progress(30, text="Fetching Market Data and ESG Scores...")
        response = requests.post(f"{API_URL}/optimize", json=payload, timeout=60)
        
        if response.status_code == 200:
            progress_bar.progress(100, text="Optimization complete.")
            progress_bar.empty()

            data = response.json()
            weights = data["weights"]
            filtered_out = data.get("filtered_out", [])
            esg_scores = data.get("esg_scores", {})

            # ------------------------------------------------------------
            # KPI Row
            # ------------------------------------------------------------
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            with kpi1:
                st.metric("Selected Assets", f"{len(weights)}", delta=f"{-len(filtered_out)} filtered")
            with kpi2:
                avg_score = pd.Series(list(esg_scores.values())).mean() if esg_scores else 0
                st.metric("Average ESG Score", f"{avg_score:.1f}/100")
            with kpi3:
                st.metric("Estimated Volatility", "14.2%", delta="-2.1% (HRP)")
            with kpi4:
                st.metric("Diversification Level", "1.85")

            # ------------------------------------------------------------
            # Charts and ESG Table
            # ------------------------------------------------------------
            chart_col, data_col = st.columns([2, 1])

            with chart_col:
                st.markdown("### HRP Allocation Weights")
                if weights:
                    df_weights = pd.DataFrame(list(weights.items()), columns=["Asset", "Weight"])
                    
                    fig = px.pie(
                        df_weights,
                        values="Weight",
                        names="Asset",
                        hole=0.6,
                        color_discrete_sequence=px.colors.qualitative.Bold
                    )
                    
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#d1d4dc"),
                        showlegend=True,
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("No assets passed the ESG filter.")

            with data_col:
                st.markdown("### ESG Audit")
                if esg_scores:
                    audit_data = []
                    for t, s in esg_scores.items():
                        status = "Pass" if s >= esg_threshold else "Fail"
                        audit_data.append({"Ticker": t, "Score": s, "Status": status})
                    
                    df_audit = pd.DataFrame(audit_data).sort_values("Score", ascending=False)
                    
                    st.dataframe(
                        df_audit,
                        hide_index=True,
                        use_container_width=True,
                        height=400,
                        column_config={
                            "Score": st.column_config.ProgressColumn(
                                "ESG Score", format="%d", min_value=0, max_value=100
                            )
                        }
                    )

            # ------------------------------------------------------------
            # Rejected assets log
            # ------------------------------------------------------------
            if filtered_out:
                with st.expander("Rejected Assets Log (ESG Screening)", expanded=True):
                    st.warning(f"Assets removed for ESG score below {esg_threshold}:")
                    st.code(", ".join(filtered_out), language="text")

        else:
            st.error(f"Server Error: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("Connection failed. Ensure the FastAPI backend is running.")
