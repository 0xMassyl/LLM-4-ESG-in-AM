import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import json

# =================================================
# Page configuration
# We define global UI parameters for the Streamlit app
# =================================================
st.set_page_config(
    page_title="Veritas Quant | Pro Terminal",
    layout="wide",                     # Use full screen width
    initial_sidebar_state="expanded",  # Sidebar opened by default
    page_icon="📈"                     # Title icon
)

# =================================================
# Custom CSS
# We override Streamlit default style to match
# a professional look
# =================================================
st.markdown("""
    <style>
        .stApp { background-color: #131722; }
        [data-testid="stSidebar"] { background-color: #1e222d; border-right: 1px solid #2a2e39; }
        h1, h2, h3, p, label, div, span { color: #d1d4dc !important; font-family: 'Roboto', sans-serif; }
        .stTextInput input, .stSelectbox div, .stNumberInput input {
            color: #d1d4dc !important;
            background-color: #2a2e39 !important;
            border: 1px solid #434651 !important;
        }
        .stButton > button {
            background-color: #2962ff !important;
            color: white !important;
            border: none;
            font-weight: 600;
        }
        [data-testid="stDataFrame"] {
            background-color: #1e222d;
            border: 1px solid #2a2e39;
        }
        [data-testid="stMetricValue"] {
            font-size: 26px;
            color: #d1d4dc !important;
        }
        .js-plotly-plot .plotly .main-svg {
            background: rgba(0,0,0,0) !important;
        }
    </style>
""", unsafe_allow_html=True)

# =================================================
# Backend API endpoint
# This is where optimization logic lives
# =================================================
API_URL = "http://127.0.0.1:8000"

# =================================================
# Header
# Visual branding and context for the user
# =================================================
col1, col2 = st.columns([1, 15])
with col2:
    st.markdown("# ⚡ LLM-4-ESG <span style='font-size:18px; color:#2962ff'>PRO</span>", unsafe_allow_html=True)
    st.markdown("### ESG-DRIVEN HIERARCHICAL RISK PARITY ENGINE")
st.markdown("---")

# =================================================
# Sidebar – user inputs
# All strategy parameters are centralized here
# =================================================
with st.sidebar:
    st.header("⚙️ STRATEGY SETTINGS")

    # ---- Asset universe ----
    # User selects which assets are included in the portfolio
    st.markdown("### 1. UNIVERSE")
    default_tickers = "AAPL, MSFT, GOOGL, AMZN, TSLA, XOM, CVX, PEP, KO, JNJ, NVDA"
    tickers_input = st.text_area(
        "Assets (Comma separated)",
        value=default_tickers,
        height=120
    )

    # ---- ESG filtering ----
    # Simple rule-based ESG exclusion using a score threshold
    st.markdown("### 2. ESG FILTERS")
    apply_esg = st.checkbox(
        "Activate ESG screening",
        value=True
    )
    esg_threshold = st.slider(
        "Minimum ESG score",
        0, 100, 50,
        help="Assets below this score are excluded."
    )

    # ---- Time range ----
    # Defines historical window for returns and risk estimation
    st.markdown("### 3. TIMEFRAME")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        start_date = st.date_input("Start", value=pd.to_datetime("2021-01-01"))
    with col_d2:
        end_date = st.date_input("End", value=pd.to_datetime("2024-01-01"))

    st.markdown("---")

    # Launch button triggers the whole pipeline
    launch_btn = st.button(
        "RUN OPTIMIZATION",
        type="primary",
        use_container_width=True
    )

# =================================================
# Main execution logic
# Everything below runs only after button click
# =================================================
if launch_btn:

    # Clean tickers input and normalize format
    ticker_list = [
        t.strip().upper()
        for t in tickers_input.split(",")
        if t.strip()
    ]

    # Prepare payload sent to backend
    payload = {
        "tickers": ticker_list,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "apply_esg_filter": apply_esg,
        "esg_threshold": esg_threshold
    }

    try:
        # Backend call can take time -> show spinner
        with st.spinner("Running optimization and portfolio analysis..."):
            response = requests.post(
                f"{API_URL}/optimize",
                json=payload,
                timeout=60
            )

        # =================================================
        # Successful response
        # =================================================
        if response.status_code == 200:
            data = response.json()

            # Extract main outputs
            status = data.get("status", "success")
            weights = data.get("weights", {})
            filtered_out = data.get("filtered_out", [])
            esg_scores = data.get("esg_scores", {})

            # Inform user if data is simulated or live
            if "simulated" in status or "error" in status:
                st.warning(
                    "Demo mode enabled. "
                    "Optimization is based on simulated market data."
                )
            else:
                st.success("Live data detected. Optimization completed successfully.")

            # Backtest data and metrics
            perf_values = data.get("performance_values", {})
            perf_dates = data.get("performance_dates", [])
            m_hrp = data.get("metrics_hrp", {})
            m_bench = data.get("metrics_bench", {})

            # =================================================
            # Section 1 – Historical performance
            # Compare HRP vs simple equal-weight benchmark
            # =================================================
            if perf_values and perf_dates:
                st.markdown("### 📈 Historical Performance (Backtest)")

                k1, k2, k3, k4 = st.columns(4)

                # Display key risk/return metrics
                with k1:
                    st.metric("Total Return", m_hrp.get("Total Return", "N/A"),
                              delta=f"vs {m_bench.get('Total Return', 'N/A')}")
                with k2:
                    st.metric("Sharpe Ratio", m_hrp.get("Sharpe Ratio", "N/A"),
                              delta=f"vs {m_bench.get('Sharpe Ratio', 'N/A')}")
                with k3:
                    st.metric("Annual Volatility", m_hrp.get("Annual Volatility", "N/A"),
                              delta=f"vs {m_bench.get('Annual Volatility', 'N/A')}",
                              delta_color="inverse")
                with k4:
                    st.metric("Max Drawdown", m_hrp.get("Max Drawdown", "N/A"),
                              delta=f"vs {m_bench.get('Max Drawdown', 'N/A')}",
                              delta_color="inverse")

                # Build cumulative performance dataframe
                df_perf = pd.DataFrame(perf_values)
                df_perf["Date"] = pd.to_datetime(perf_dates)
                df_perf = df_perf.set_index("Date")

                # Plot performance curves
                fig_perf = px.line(
                    df_perf,
                    x=df_perf.index,
                    y=df_perf.columns
                )

                fig_perf.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#d1d4dc"),
                    yaxis_title="Cumulative Return (Base 100)",
                    hovermode="x unified",
                    height=350
                )

                st.plotly_chart(fig_perf, use_container_width=True)
                st.markdown("---")

            # =================================================
            # Section 2 – Allocation and ESG audit
            # Shows final portfolio composition and ESG scores
            # =================================================
            col_chart, col_data = st.columns([1, 1])

            with col_chart:
                st.markdown("### 📊 HRP Allocation Weights")

                if weights:
                    df_w = pd.DataFrame(
                        list(weights.items()),
                        columns=["Asset", "Weight"]
                    )

                    fig_p = px.pie(
                        df_w,
                        values="Weight",
                        names="Asset",
                        hole=0.6
                    )

                    fig_p.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#d1d4dc"),
                        height=350
                    )

                    st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.error("No assets passed the ESG filter.")

            with col_data:
                st.markdown("### 📋 ESG Governance Scores")

                if esg_scores:
                    audit_data = []

                    # Build ESG audit table
                    for ticker, score in esg_scores.items():
                        audit_data.append({
                            "Ticker": ticker,
                            "Score": score,
                            "Status": "PASS" if score >= esg_threshold else "REJECT"
                        })

                    df_s = pd.DataFrame(audit_data).sort_values("Score", ascending=False)

                    st.dataframe(
                        df_s,
                        hide_index=True,
                        use_container_width=True,
                        height=350
                    )

            # =================================================
            # Section 3 – Rejected assets log
            # Transparency on exclusions
            # =================================================
            if filtered_out:
                with st.expander("🔻 Rejected Assets Log", expanded=True):
                    st.warning(
                        f"Assets excluded due to ESG score below {esg_threshold}"
                    )
                    st.code(", ".join(filtered_out), language="text")

        else:
            st.error(f"Server error: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("Connection failed. Backend is not reachable.")
    except Exception as e:
        st.error(f"Unexpected error: {e}")
