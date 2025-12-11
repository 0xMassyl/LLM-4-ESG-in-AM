import pandas as pd
import numpy as np

def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Computes robust log-returns without aggressively dropping rows.
    Missing values are forward-filled to avoid breaking the return series.
    """
    # 1. Ensure chronological ordering
    prices = prices.sort_index()

    # 2. Forward-fill missing values to preserve continuity
    prices_filled = prices.ffill()

    # 3. Compute raw ratio P_t / P_(t-1)
    raw_returns = prices_filled / prices_filled.shift(1)

    # 4. Replace infinities produced by division by zero
    raw_returns = raw_returns.replace([np.inf, -np.inf], np.nan)

    # 5. Convert ratios into log-returns: ln(P_t / P_(t-1))
    log_returns_df = pd.DataFrame(np.log(raw_returns))

    # 6. Replace remaining NaN values with 0.0
    # This prevents the return matrix from collapsing when sparse data is present.
    log_returns_df = log_returns_df.fillna(0.0)

    # Drop the first row (always NaN/0.0 due to the initial shift)
    return log_returns_df.iloc[1:]


def get_covariance_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the annualized covariance matrix using 252 trading days.
    """
    return returns.cov() * 252


def get_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the correlation matrix of asset returns.
    """
    return returns.corr()
