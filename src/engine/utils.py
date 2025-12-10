import pandas as pd
import numpy as np


def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Computes log-returns from a price series.

    Log-returns are preferred in quantitative finance because:
      - they are time-additive (log returns sum across periods),
      - they align better with statistical models assuming normality,
      - they remain stable even when absolute price levels differ widely.

    Formula:
        r_t = ln(P_t / P_{t-1})

    The implementation applies a one-step shift to align prices and then
    computes the natural log safely over the entire DataFrame.
    """
    raw_returns = prices / prices.shift(1)
    log_returns_df = pd.DataFrame(np.log(raw_returns))

    # Removes the first row, which cannot produce a valid return.
    return log_returns_df.dropna()


def get_covariance_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the annualized covariance matrix of asset returns.

    The scaling factor (252) approximates the number of trading days in a year,
    making the output suitable for most risk management or portfolio models.
    """
    return returns.cov() * 252


def get_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the correlation matrix of asset returns.

    Correlations describe linear dependence between assets, ranging from -1 to 1.
    They are fundamental in clustering-based allocation methods such as HRP.
    """
    return returns.corr()
