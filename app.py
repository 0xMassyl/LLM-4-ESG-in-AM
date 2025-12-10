import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Veritas Quant | Pro Terminal",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# --- TRADINGVIEW CSS HACK ---
# This CSS forces the Dark Mode / Neon look regardless of user settings
st.markdown("""
    <style>
        /* Main Background */
        .stApp {
            background-color: #131722;
        }
        
        /* Sidebar Background */
        [data-testid="stSidebar"] {
            background-color: #1e222d;
            border-right: 1px solid #2a2e39;
        }
        
        /* Text Colors */
        h1, h2, h3, p, label, div, span {
            color: #d1d4dc !important;
            font-family: 'Roboto', sans-serif;
        }
        
        /* Input Fields Styling */
        .stTextInput input, .stSelectbox div, .stNumberInput input {
            color: #d1d4dc !important;
            background-color: #2a2e39 !important;
            border: 1px solid #434651 !important;
        }
        
        /* Buttons (TradingView Blue) */
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
        
        /* Tables */
        [data-testid="stDataFrame"] {
            background-color: #1e222d;
            border: 1px solid #2a2e39;
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            font-size: 26px;
            color: #d1d4dc !important;
        }
        [data-testid="stMetricDelta"] svg {
            fill: #d1d4dc !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- API Connection ---
API_URL = "http://127.0.0.1:8000"

# --- HEADER SECTION ---
col_logo, col_title = st.columns([1, 15])
with col_title:
    st.markdown("# ⚡ VERITAS QUANT <span style='font-size:18px; color:#2962ff'>PRO</span>", unsafe_allow_html=True)
    st.markdown("### ESG-DRIVEN HIERARCHICAL RISK PARITY ENGINE")

st.markdown("---")

# --- SIDEBAR: CONTROLS ---
with st.sidebar:
    st.header("⚙️ STRATEGY SETTINGS")
    
    st.markdown("### 1. UNIVERSE")
    default_tickers = "AAPL, MSFT, GOOGL, AMZN, TSLA, XOM, CVX, PEP, KO, JNJ, NVDA"
    tickers_input = st.text_area("Assets (Comma separated)", value=default_tickers, height=100)

    st.markdown("### 2. ESG FILTERS (AI)")
    apply_esg = st.checkbox("Active ESG Screening", value=True)
    esg_threshold = st.slider("Min. ESG Score", 0, 100, 50)
    
    st.markdown("### 3. TIMEFRAME")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Start", value=pd.to_datetime("2021-01-01"))
    with col_d2:
        end_date = st.date_input("End", value=pd.to_datetime("2024-01-01"))
    
    st.markdown("---")
    launch_btn = st.button("RUN OPTIMIZATION", type="primary", use_container_width=True)

# --- MAIN EXECUTION ---
if launch_btn:
    # Prepare Payload
    ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    
    payload = {
        "tickers": ticker_list,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "apply_esg_filter": apply_esg,
        "esg_threshold": esg_threshold
    }

    # Progress Bar
    progress_bar = st.progress(0, text="Initializing Quant Engine...")

    try:
        # API Call
        progress_bar.progress(30, text="Fetching Market Data & AI Scores...")
        response = requests.post(f"{API_URL}/optimize", json=payload, timeout=60)
        
        if response.status_code == 200:
            progress_bar.progress(100, text="Optimization Complete.")
            progress_bar.empty()
            
            data = response.json()
            weights = data["weights"]
            filtered_out = data.get("filtered_out", [])
            esg_scores = data.get("esg_scores", {})

            # --- ROW 1: KPI CARDS ---
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            # Simulated financial metrics for the UI demo
            with kpi1:
                st.metric("Selected Assets", f"{len(weights)}", delta=f"-{len(filtered_out)} Rejected", delta_color="inverse")
            with kpi2:
                avg_score = pd.Series(list(esg_scores.values())).mean() if esg_scores else 0
                st.metric("Portfolio ESG", f"{avg_score:.1f}/100", delta="+12% vs Bench")
            with kpi3:
                st.metric("Est. Volatility", "14.2%", delta="-2.1% (HRP)", delta_color="normal")
            with kpi4:
                st.metric("Diversification", "1.85", delta="High")

            st.write("") # Spacer

            # --- ROW 2: CHARTS & TABLES ---
            chart_col, data_col = st.columns([2, 1])

            with chart_col:
                st.markdown("### 📊 HRP Allocation Weights")
                if weights:
                    df_weights = pd.DataFrame(list(weights.items()), columns=["Asset", "Weight"])
                    
                    # Donut Chart with Dark Theme
                    fig = px.pie(df_weights, values='Weight', names='Asset', hole=0.6,
                                 color_discrete_sequence=px.colors.qualitative.Bold)
                    
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#d1d4dc"),
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="top", y=1, xanchor="right"),
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error("No assets survived the ESG filter.")

            with data_col:
                st.markdown("### 📋 ESG Governance")
                if esg_scores:
                    audit_data = []
                    for t, s in esg_scores.items():
                        status = "✅" if s >= esg_threshold else "❌"
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

            # --- ROW 3: LOGS ---
            if filtered_out:
                with st.expander("🔻 Rejected Assets Log (AI Decision)", expanded=True):
                    st.warning(f"The following assets were excluded due to low ESG scores (<{esg_threshold}):")
                    st.code(", ".join(filtered_out), language="text")

        else:
            st.error(f"❌ Server Error: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection Failed. Is the FastAPI backend running?")