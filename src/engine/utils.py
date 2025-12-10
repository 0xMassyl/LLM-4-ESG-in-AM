import pandas as pd
import numpy as np


def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Computes log-returns from price data.
    
    Log-returns are often used in quantitative finance because:
      - they make time aggregation easier (returns add up),
      - they behave better under statistical models,
      - they avoid issues when price levels vary significantly across assets.

    Formula:
        r_t = ln(P_t / P_{t-1})

    The implementation uses a simple shift to align prices and
    then applies the logarithm safely on a DataFrame.
    """
    # raw_returns contains the ratio P_t / P_{t-1}
    raw_returns = prices / prices.shift(1)

    # np.log keeps the DataFrame structure, but we wrap it in a DataFrame
    # to satisfy strict type checkers.
    log_returns_df = pd.DataFrame(np.log(raw_returns))

    # dropna removes the first row (which has no previous price)
    return log_returns_df.dropna()


def get_covariance_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the annualized covariance matrix of asset returns.
    Covariance is scaled by 252 to approximate yearly risk
    (assuming ~252 trading days in a year).

    This matrix is a key input for risk models and allocation methods.
    """
    return returns.cov() * 252


def get_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the correlation matrix of returns.
    Correlations range from -1 to 1 and help identify relationships
    between assets (e.g., clustering in HRP).

    This function is frequently used during risk decomposition steps.
    """
    return returns.corr()
