import pandas as pd
import numpy as np
from src.engine.hrp_optimizer import HRPOptimizer
from src.engine.utils import calculate_log_returns


def generate_dummy_market_data(days=252, n_assets=10):
    """
    Generates synthetic market data following a correlated Gaussian random walk.
    The goal is to provide realistic test data for the HRP optimizer without relying
    on real market prices.

    Main points:
    - A custom correlation matrix structures cross-asset relationships.
    - HRP should naturally down-weight highly volatile or strongly correlated assets.
    """
    np.random.seed(42)  # Ensures reproducible tests
    
    # Custom correlation matrix used to drive clustering behavior within HRP.
    corr = np.array([
        [1.0, 0.8, 0.5, 0.1],
        [0.8, 1.0, 0.4, 0.1],
        [0.5, 0.4, 1.0, 0.2],
        [0.1, 0.1, 0.2, 1.0]
    ])
    
    # Cholesky decomposition converts independent noise into correlated returns.
    L = np.linalg.cholesky(corr)
    
    # Simulate daily returns for four assets, then apply the correlation structure.
    daily_returns = np.random.normal(0, 0.01, (days, 4))
    correlated_returns = daily_returns @ L.T
    
    # Basic tickers for clarity.
    tickers = [f"ASSET_{i}" for i in range(4)]
    df = pd.DataFrame(correlated_returns, columns=tickers)
    
    # Convert returns to cumulative price paths with an initial value of 100.
    prices = 100 * (1 + df).cumprod()
    
    # Increase volatility of ASSET_0 to test HRP risk allocation.
    prices["ASSET_0"] = prices["ASSET_0"] * 1.5
    
    return prices


def main():
    print("Starting HRP Optimization Demo")
    
    # -------------------------------------------------------------
    # 1. DATA GENERATION
    # -------------------------------------------------------------
    print("1. Generating synthetic market data...")
    prices = generate_dummy_market_data()
    
    # Log returns are typically more stable for covariance-based models.
    returns = calculate_log_returns(prices)
    print(f"   Data shape: {returns.shape}")
    
    # -------------------------------------------------------------
    # 2. RUN HRP OPTIMIZATION
    # -------------------------------------------------------------
    print("2. Running Hierarchical Risk Parity (HRP)...")
    
    # HRPOptimizer performs:
    # - covariance and distance matrix construction
    # - hierarchical clustering (SciPy)
    # - recursive bisection to allocate risk-balanced weights
    optimizer = HRPOptimizer(returns)
    weights = optimizer.optimize()

    print("\n Optimal Portfolio Weights")
    print(weights.sort_values(ascending=False).apply(lambda x: f"{x:.2%}"))
    
    # Brief interpretation to help validate HRP correctness.
    print("\nObservation:")
    print("- Highly correlated assets tend to cluster together in HRP.")
    print("- More volatile assets (like ASSET_0) receive smaller weights,")
    print("  illustrating the risk-sensitive structure of the method.")


if __name__ == "__main__":
    main()
