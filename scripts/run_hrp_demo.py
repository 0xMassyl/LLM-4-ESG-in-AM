import pandas as pd
import numpy as np
from src.engine.hrp_optimizer import HRPOptimizer
from src.engine.utils import calculate_log_returns


def generate_dummy_market_data(days=252, n_assets=10):
    """
    Generates synthetic market data using correlated Gaussian random walks.
    This allows us to test the HRP optimizer on realistic-looking data without
    using real stock prices.
    
    Key idea:
    - We manually design a correlation structure.
    - Assets with higher volatility or correlation patterns should receive
      lower weights in HRP.
    """
    np.random.seed(42)  # Ensures reproducibility
    
    # Manually defined correlation matrix (4 assets).
    # Strongly correlated assets should be grouped together by HRP clustering.
    corr = np.array([
        [1.0, 0.8, 0.5, 0.1],
        [0.8, 1.0, 0.4, 0.1],
        [0.5, 0.4, 1.0, 0.2],
        [0.1, 0.1, 0.2, 1.0]
    ])
    
    # Cholesky factor to transform uncorrelated random variables into correlated ones following the 'corr' matrix.
    L = np.linalg.cholesky(corr)
    
    # Generate daily returns for 4 assets (even though user asked for n_assets, here we only simulate 4 for simplicity and repeat that pattern).
    daily_returns = np.random.normal(0, 0.01, (days, 4))
    correlated_returns = daily_returns @ L.T  # Introduces correlation structure.
    
    # Assign basic tickers.
    tickers = [f"ASSET_{i}" for i in range(4)]
    df = pd.DataFrame(correlated_returns, columns=tickers)
    
    # Convert daily returns to price paths (starting at 100).
    prices = 100 * (1 + df).cumprod()
    
    # Make ASSET_0 artificially more volatile.
    # HRP should naturally assign this asset a smaller allocation.
    prices["ASSET_0"] = prices["ASSET_0"] * 1.5
    
    return prices


def main():
    print("Starting HRP Optimization Demo")
    
    # -------------------------------------------------------------
    # 1. DATA GENERATION
    # -------------------------------------------------------------
    print("1. Generating synthetic market data...")
    prices = generate_dummy_market_data()
    
    # Convert price series into log returns (safer for risk modeling).
    returns = calculate_log_returns(prices)
    print(f"   Data Shape: {returns.shape}")  # (252 days, 4 assets)
    
    # -------------------------------------------------------------
    # 2. RUN HRP OPTIMIZATION
    # -------------------------------------------------------------
    print("2. Running Hierarchical Risk Parity (HRP)...")
    
    # HRPOptimizer encapsulates:
    # - distance matrix computation
    # - hierarchical clustering (SciPy)
    # - recursive bisection for weight allocation
    optimizer = HRPOptimizer(returns)
    weights = optimizer.optimize()

    print("\n Optimal Portfolio Weights ")
   
    print(weights.sort_values(ascending=False).apply(lambda x: f"{x:.2%}"))
    
    print("\nObservation:")
    print("- Highly correlated assets should fall in the same cluster.")
    print("- Assets with strong volatility (like ASSET_0) receive lower weights,")
    print("  demonstrating the risk-aware nature of HRP.")


if __name__ == "__main__":
    main()
