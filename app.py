import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import json

# --- Page Configuration ---
st.set_page_config(
    page_title="Veritas Quant | Pro Terminal",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📈"
)

# --- CSS STYLE ---
st.markdown("""
    <style>
        .stApp { background-color: #131722; }
        [data-testid="stSidebar"] { background-color: #1e222d; border-right: 1px solid #2a2e39; }
        h1, h2, h3, p, label, div, span { color: #d1d4dc !important; font-family: 'Roboto', sans-serif; }
        .stTextInput input, .stSelectbox div, .stNumberInput input { color: #d1d4dc !important; background-color: #2a2e39 !important; border: 1px solid #434651 !important; }
        .stButton > button { background-color: #2962ff !important; color: white !important; border: none; font-weight: 600; }
        [data-testid="stDataFrame"] { background-color: #1e222d; border: 1px solid #2a2e39; }
        [data-testid="stMetricValue"] { font-size: 26px; color: #d1d4dc !important; }
        .js-plotly-plot .plotly .main-svg { background: rgba(0,0,0,0) !important; }
    </style>
""", unsafe_allow_html=True)

API_URL = "http://127.0.0.1:8000"

# --- HEADER ---
col1, col2 = st.columns([1, 15])
with col2:
    st.markdown("# ⚡ LLM-4-ESG <span style='font-size:18px; color:#2962ff'>PRO</span>", unsafe_allow_html=True)
    st.markdown("### ESG-DRIVEN HIERARCHICAL RISK PARITY ENGINE")
st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ STRATEGY SETTINGS")
    
    st.markdown("### 1. UNIVERSE")
    default_tickers = "AAPL, MSFT, GOOGL, AMZN, TSLA, XOM, CVX, PEP, KO, JNJ, NVDA"
    tickers_input = st.text_area("Assets (Comma separated)", value=default_tickers, height=120)
    
    st.markdown("### 2. ESG FILTERS (AI)")
    apply_esg = st.checkbox("Active ESG Screening", value=True)
    esg_threshold = st.slider("Min. ESG Score", 0, 100, 50, help="Exclude assets below this AI-generated score.")
    
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
    ticker_list = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    
    payload = {
        "tickers": ticker_list,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "apply_esg_filter": apply_esg,
        "esg_threshold": esg_threshold
    }

    try:
        with st.spinner("🤖 Running AI Analysis & HRP Optimization..."):
            response = requests.post(f"{API_URL}/optimize", json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status", "success") # Récupère le statut
            weights = data["weights"]
            filtered_out = data["filtered_out"]
            esg_scores = data["esg_scores"]
            
            # Affichage du statut d'opération (Feedback visuel amélioré)
            if "simulated" in status or "error" in status:
                st.warning(f"⚠️ MODE DÉMO ACTIVÉ : {status.replace('simulated: ', '').replace('error: ', '')}. Le calcul HRP utilise des données simulées pour la continuité de service.")
            else:
                st.success("✅ DONNÉES RÉELLES : Optimisation HRP lancée sur l'univers filtré.")

            # Données Backtest
            perf_values = data.get("performance_values", {})
            perf_dates = data.get("performance_dates", [])
            m_hrp = data.get("metrics_hrp", {})
            m_bench = data.get("metrics_bench", {})

            # ---------------------------------------------------------
            # SECTION 1: HISTORICAL PERFORMANCE (BACKTEST)
            # ---------------------------------------------------------
            if perf_values and perf_dates:
                st.markdown("### 📈 Historical Performance (Backtest)")
                
                # KPI Cards
                k1, k2, k3, k4 = st.columns(4)
                
                with k1: 
                    st.metric("Total Return", m_hrp.get("Total Return", "N/A"), delta=f"vs {m_bench.get('Total Return', 'N/A')}")
                with k2: 
                    st.metric("Sharpe Ratio", m_hrp.get("Sharpe Ratio", "N/A"), delta=f"vs {m_bench.get('Sharpe Ratio', 'N/A')}")
                with k3: 
                    st.metric("Annual Volatility", m_hrp.get("Annual Volatility", "N/A"), 
                              delta=f"vs {m_bench.get('Annual Volatility', 'N/A')}", delta_color="inverse")
                with k4: 
                    st.metric("Max Drawdown", m_hrp.get("Max Drawdown", "N/A"), 
                              delta=f"vs {m_bench.get('Max Drawdown', 'N/A')}", delta_color="inverse")

                # Graphique de Performance
                df_perf = pd.DataFrame(perf_values)
                df_perf['Date'] = pd.to_datetime(perf_dates)
                df_perf = df_perf.set_index('Date')
                
                fig_perf = px.line(df_perf, x=df_perf.index, y=df_perf.columns, 
                                   color_discrete_map={"Veritas HRP": "#2962ff", "Benchmark (1/N)": "#787b86"})
                
                fig_perf.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", 
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#d1d4dc"),
                    xaxis_title="", 
                    yaxis_title="Cumulative Return (Base 100)",
                    legend=dict(orientation="h", y=1.1, title=""),
                    hovermode="x unified",
                    height=350
                )
                st.plotly_chart(fig_perf, use_container_width=True)
                st.markdown("---")

            # ---------------------------------------------------------
            # SECTION 2: ALLOCATION & ESG AUDIT
            # ---------------------------------------------------------
            col_chart, col_data = st.columns([1, 1])

            with col_chart:
                st.markdown("### 📊 HRP Allocation Weights")
                if weights:
                    df_w = pd.DataFrame(list(weights.items()), columns=["Asset", "Weight"])
                    
                    fig_p = px.pie(df_w, values="Weight", names="Asset", hole=0.6, 
                                   color_discrete_sequence=px.colors.qualitative.Bold)
                    
                    fig_p.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#d1d4dc"),
                        showlegend=True,
                        legend=dict(orientation="v", yanchor="middle", xanchor="left", x=1.0),
                        margin=dict(t=20, b=20, l=20, r=20),
                        height=350
                    )
                    st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.error("No assets survived the ESG filter.")

            with col_data:
                st.markdown("### 📋 ESG Governance (AI Scoring)")
                if esg_scores:
                    audit_data = []
                    for t, s in esg_scores.items():
                        status = "✅ PASS" if s >= esg_threshold else "❌ REJECT"
                        audit_data.append({"Ticker": t, "Score": s, "Status": status})
                    
                    df_s = pd.DataFrame(audit_data).sort_values("Score", ascending=False)
                    
                    st.dataframe(
                        df_s, 
                        hide_index=True, 
                        use_container_width=True, 
                        height=350,
                        column_config={
                            "Score": st.column_config.ProgressColumn(
                                "AI Score", min_value=0, max_value=100, format="%d"
                            )
                        }
                    )

            # ---------------------------------------------------------
            # SECTION 3: LOGS
            # ---------------------------------------------------------
            if filtered_out:
                with st.expander("🔻 Rejected Assets Log (AI Decision)", expanded=True):
                    st.warning(f"The following assets were excluded due to low ESG scores (<{esg_threshold}):")
                    st.code(", ".join(filtered_out), language="text")

        else:
            st.error(f"❌ Server Error: {response.text}")

    except requests.exceptions.ConnectionError:
        st.error("🔌 Connection Failed. Is the FastAPI backend running on port 8000?")
    except Exception as e:
        st.error(f"⚠️ An unexpected error occurred: {e}")