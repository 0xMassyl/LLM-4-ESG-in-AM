import pandas as pd
import numpy as np
from typing import Dict, Any, cast

def run_backtest(returns: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
    """
    Simulates historical portfolio performance using a base value of 100.
    Produces both the HRP strategy curve and a simple equal-weight benchmark.
    """
    # 1. Strict cleanup of the return matrix
    returns_clean = returns.apply(pd.to_numeric, errors="coerce").fillna(0.0)

    # 2. Weight alignment: ensures missing tickers get a zero weight
    weights_series = pd.Series(weights).reindex(returns_clean.columns).fillna(0.0)

    # 3. Weighted daily portfolio returns
    portfolio_returns = (returns_clean * weights_series).sum(axis=1)

    # 4. Equal-weight benchmark
    benchmark_returns = returns_clean.mean(axis=1)

    # 5. Cumulative performance curves (Base 100)
    strategy_curve = 100 * (1 + portfolio_returns).cumprod()
    benchmark_curve = 100 * (1 + benchmark_returns).cumprod()

    return pd.DataFrame({
        "Veritas HRP": strategy_curve,
        "Benchmark (1/N)": benchmark_curve
    })

def calculate_metrics(daily_returns: pd.Series) -> Dict[str, Any]:
    """
    Computes standard performance metrics:
    - Total return
    - Annualized volatility
    - Sharpe ratio
    - Maximum drawdown

    Uses `cast` to ensure compatibility between Pandas scalars and Python floats.
    """
    # Handles empty input gracefully
    if daily_returns.empty:
        return {
            "Total Return": "0.00%",
            "Annual Volatility": "0.00%",
            "Sharpe Ratio": "0.00",
            "Max Drawdown": "0.00%"
        }

    # Cleanup: ensures all values are numeric
    r = pd.to_numeric(daily_returns, errors="coerce").fillna(0.0)

    # --- TOTAL RETURN ---
    total_return_raw = (1 + r).prod()
    total_return = float(cast(float, total_return_raw)) - 1.0

    # --- ANNUALIZED VOLATILITY ---
    std_dev = r.std()
    annual_vol = float(cast(float, std_dev)) * np.sqrt(252)

    # --- SHARPE RATIO ---
    mean_ret = r.mean()
    mean_ret_ann = float(cast(float, mean_ret)) * 252
    risk_free_rate = 0.02  # Constant assumption for simplicity

    if annual_vol == 0:
        sharpe = 0.0
    else:
        sharpe = (mean_ret_ann - risk_free_rate) / annual_vol

    # --- MAXIMUM DRAWDOWN ---
    cum_ret = (1 + r).cumprod()
    peak = cum_ret.expanding(min_periods=1).max()
    drawdown = (cum_ret / peak) - 1.0
    max_dd = float(cast(float, drawdown.min()))

    return {
        "Total Return": f"{total_return:.2%}",
        "Annual Volatility": f"{annual_vol:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Max Drawdown": f"{max_dd:.2%}"
    }
