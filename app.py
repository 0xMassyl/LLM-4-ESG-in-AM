# -------------------------------------------------
# Core Streamlit library
# Used to build the frontend UI
# -------------------------------------------------
import streamlit as st

# -------------------------------------------------
# Data manipulation
# Used to format tables and time series
# -------------------------------------------------
import pandas as pd

# -------------------------------------------------
# HTTP client
# Used to communicate with the FastAPI backend
# -------------------------------------------------
import requests

# -------------------------------------------------
# Plotting library
# Used for interactive charts
# -------------------------------------------------
import plotly.express as px

# -------------------------------------------------
# JSON utility (explicit import for clarity/debugging)
# -------------------------------------------------
import json


# =================================================
# PAGE CONFIGURATION
# =================================================
# This defines global UI behavior for the Streamlit app.
# It must be called once, at the very top of the file.
# =================================================
st.set_page_config(
    page_title="Veritas Quant | Pro Terminal",  # Browser tab title
    layout="wide",                             # Use full screen width
    initial_sidebar_state="expanded",          # Sidebar visible by default
    page_icon="📈"                             # Icon shown in browser tab
)


# =================================================
# CUSTOM CSS
# =================================================
# Streamlit has limited styling options.
# We inject raw CSS to enforce a professional
# dark-theme trading terminal look.
# =================================================
st.markdown("""
    <style>
        /* Global background */
        .stApp { background-color: #131722; }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #1e222d;
            border-right: 1px solid #2a2e39;
        }

        /* Global text styling */
        h1, h2, h3, p, label, div, span {
            color: #d1d4dc !important;
            font-family: 'Roboto', sans-serif;
        }

        /* Inputs styling */
        .stTextInput input,
        .stSelectbox div,
        .stNumberInput input {
            color: #d1d4dc !important;
            background-color: #2a2e39 !important;
            border: 1px solid #434651 !important;
        }

        /* Primary buttons */
        .stButton > button {
            background-color: #2962ff !important;
            color: white !important;
            border: none;
            font-weight: 600;
        }

        /* Tables */
        [data-testid="stDataFrame"] {
            background-color: #1e222d;
            border: 1px solid #2a2e39;
        }

        /* KPI metrics */
        [data-testid="stMetricValue"] {
            font-size: 26px;
            color: #d1d4dc !important;
        }

        /* Plotly background */
        .js-plotly-plot .plotly .main-svg {
            background: rgba(0,0,0,0) !important;
        }
    </style>
""", unsafe_allow_html=True)


# =================================================
# BACKEND API ENDPOINT
# =================================================
# This is the only coupling point between
# the Streamlit frontend and the FastAPI backend.
# =================================================
API_URL = "http://127.0.0.1:8000"


# =================================================
# HEADER SECTION
# =================================================
# Top branding area of the application.
# Gives context before user interaction.
# =================================================
col1, col2 = st.columns([1, 15])  # Layout split (icon / text)

with col2:
    # Main title
    st.markdown(
        "# ⚡ LLM-4-ESG <span style='font-size:18px; color:#2962ff'>PRO</span>",
        unsafe_allow_html=True
    )

    # Subtitle explaining what the app actually does
    st.markdown("### ESG-DRIVEN HIERARCHICAL RISK PARITY ENGINE")

# Horizontal separator
st.markdown("---")


# =================================================
# SIDEBAR – STRATEGY INPUTS
# =================================================
# The sidebar acts as the control panel.
# All user decisions that affect the backend
# are made here.
# =================================================
with st.sidebar:

    # Sidebar title
    st.header("⚙️ STRATEGY SETTINGS")

    # ---------------------------------------------
    # 1. ASSET UNIVERSE
    # ---------------------------------------------
    # Defines which assets will be sent to the backend.
    # ---------------------------------------------
    st.markdown("### 1. UNIVERSE")

    # Default tickers shown on first load
    default_tickers = (
        "AAPL, MSFT, GOOGL, AMZN, TSLA, "
        "XOM, CVX, PEP, KO, JNJ, NVDA"
    )

    # Multiline text input allows flexible universe editing
    tickers_input = st.text_area(
        "Assets (Comma separated)",
        value=default_tickers,
        height=120
    )

    # ---------------------------------------------
    # 2. ESG FILTERING
    # ---------------------------------------------
    # Controls ESG exclusion logic in the backend.
    # ---------------------------------------------
    st.markdown("### 2. ESG FILTERS")

    # Boolean toggle to activate/deactivate ESG filtering
    apply_esg = st.checkbox(
        "Activate ESG screening",
        value=True
    )

    # ESG score threshold
    # Assets below this value will be excluded
    esg_threshold = st.slider(
        "Minimum ESG score",
        0, 100, 50,
        help="Assets below this score are excluded."
    )

    # ---------------------------------------------
    # 3. TIMEFRAME
    # ---------------------------------------------
    # Defines historical window used for returns,
    # risk estimation and backtesting.
    # ---------------------------------------------
    st.markdown("### 3. TIMEFRAME")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        start_date = st.date_input(
            "Start",
            value=pd.to_datetime("2021-01-01")
        )

    with col_d2:
        end_date = st.date_input(
            "End",
            value=pd.to_datetime("2024-01-01")
        )

    st.markdown("---")

    # ---------------------------------------------
    # RUN BUTTON
    # ---------------------------------------------
    # This is the only trigger for backend execution.
    # No auto-refresh, no hidden calls.
    # ---------------------------------------------
    launch_btn = st.button(
        "RUN OPTIMIZATION",
        type="primary",
        use_container_width=True
    )


# =================================================
# MAIN EXECUTION LOGIC
# =================================================
# Everything below runs ONLY after user clicks
# the "RUN OPTIMIZATION" button.
# =================================================
if launch_btn:

    # ---------------------------------------------
    # Clean and normalize tickers input
    # ---------------------------------------------
    # - remove whitespace
    # - enforce uppercase
    # - remove empty values
    ticker_list = [
        t.strip().upper()
        for t in tickers_input.split(",")
        if t.strip()
    ]

    # ---------------------------------------------
    # Build request payload for FastAPI
    # ---------------------------------------------
    payload = {
        "tickers": ticker_list,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "apply_esg_filter": apply_esg,
        "esg_threshold": esg_threshold
    }

    try:
        # -----------------------------------------
        # Backend call
        # -----------------------------------------
        # The spinner improves UX for long computations.
        with st.spinner("Running optimization and portfolio analysis..."):
            response = requests.post(
                f"{API_URL}/optimize",
                json=payload,
                timeout=60
            )

        # -----------------------------------------
        # SUCCESSFUL RESPONSE
        # -----------------------------------------
        if response.status_code == 200:

            # Parse JSON response
            data = response.json()

            # Extract core outputs
            status = data.get("status", "success")
            weights = data.get("weights", {})
            filtered_out = data.get("filtered_out", [])
            esg_scores = data.get("esg_scores", {})

            # -------------------------------------
            # Status feedback
            # -------------------------------------
            # Informs user whether data is real or simulated.
            if "simulated" in status or "error" in status:
                st.warning(
                    "Demo mode enabled. "
                    "Optimization is based on simulated market data."
                )
            else:
                st.success(
                    "Live data detected. Optimization completed successfully."
                )

            # -------------------------------------
            # Backtest data and metrics
            # -------------------------------------
            perf_values = data.get("performance_values", {})
            perf_dates = data.get("performance_dates", [])
            m_hrp = data.get("metrics_hrp", {})
            m_bench = data.get("metrics_bench", {})

            # =================================================
            # SECTION 1 – PERFORMANCE
            # =================================================
            if perf_values and perf_dates:

                st.markdown("### 📈 Historical Performance (Backtest)")

                # KPI layout
                k1, k2, k3, k4 = st.columns(4)

                # Each metric compares HRP vs benchmark
                with k1:
                    st.metric(
                        "Total Return",
                        m_hrp.get("Total Return", "N/A"),
                        delta=f"vs {m_bench.get('Total Return', 'N/A')}"
                    )

                with k2:
                    st.metric(
                        "Sharpe Ratio",
                        m_hrp.get("Sharpe Ratio", "N/A"),
                        delta=f"vs {m_bench.get('Sharpe Ratio', 'N/A')}"
                    )

                with k3:
                    st.metric(
                        "Annual Volatility",
                        m_hrp.get("Annual Volatility", "N/A"),
                        delta=f"vs {m_bench.get('Annual Volatility', 'N/A')}",
                        delta_color="inverse"
                    )

                with k4:
                    st.metric(
                        "Max Drawdown",
                        m_hrp.get("Max Drawdown", "N/A"),
                        delta=f"vs {m_bench.get('Max Drawdown', 'N/A')}",
                        delta_color="inverse"
                    )

                # Build performance DataFrame
                df_perf = pd.DataFrame(perf_values)
                df_perf["Date"] = pd.to_datetime(perf_dates)
                df_perf = df_perf.set_index("Date")

                # Plot cumulative performance
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
            # SECTION 2 – ALLOCATION & ESG AUDIT
            # =================================================
            col_chart, col_data = st.columns([1, 1])

            # -------------------------
            # Allocation pie chart
            # -------------------------
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

            # -------------------------
            # ESG audit table
            # -------------------------
            with col_data:
                st.markdown("### 📋 ESG Governance Scores")

                if esg_scores:
                    audit_data = []

                    # Build table row by row
                    for ticker, score in esg_scores.items():
                        audit_data.append({
                            "Ticker": ticker,
                            "Score": score,
                            "Status": "PASS" if score >= esg_threshold else "REJECT"
                        })

                    df_s = (
                        pd.DataFrame(audit_data)
                        .sort_values("Score", ascending=False)
                    )

                    st.dataframe(
                        df_s,
                        hide_index=True,
                        use_container_width=True,
                        height=350
                    )

            # =================================================
            # SECTION 3 – REJECTED ASSETS LOG
            # =================================================
            if filtered_out:
                with st.expander("🔻 Rejected Assets Log", expanded=True):
                    st.warning(
                        f"Assets excluded due to ESG score below {esg_threshold}"
                    )
                    st.code(", ".join(filtered_out), language="text")

        else:
            # Backend returned an HTTP error
            st.error(f"Server error: {response.text}")

    except requests.exceptions.ConnectionError:
        # Backend is unreachable
        st.error("Connection failed. Backend is not reachable.")

    except Exception as e:
        # Absolute frontend safety net
        st.error(f"Unexpected error: {e}")
