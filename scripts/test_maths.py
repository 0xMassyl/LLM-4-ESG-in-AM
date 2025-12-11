import pandas as pd
import numpy as np
from src.engine.hrp_optimizer import HRPOptimizer

def test_hrp():
    print("--- HRP ENGINE UNIT TEST ---")
    
    # 1. Generate synthetic correlated data
    # Assets A and B are highly correlated; C is uncorrelated and more volatile.
    np.random.seed(42)
    n = 1000
    
    a = np.random.normal(0, 0.01, n)
    b = a + np.random.normal(0, 0.002, n)  # B mimics A very closely
    c = np.random.normal(0, 0.02, n)       # C is independent and higher risk
    
    returns = pd.DataFrame({'A': a, 'B': b, 'C': c})
    
    print("Asset correlation matrix (A and B should be close to 1):")
    print(returns.corr().round(2))
    
    # 2. Run the HRP optimizer on the synthetic data
    optimizer = HRPOptimizer(returns)
    weights = optimizer.optimize()
    
    print("\n--- HRP RESULT (Weights) ---")
    print(weights.apply(lambda x: f"{x:.2%}"))
    
    # 3. Sanity check
    # HRP should identify (A+B) as one cluster and C as another.
    # Because C is more volatile, it should receive a lower allocation.
    # Within the A/B cluster, risk is redistributed between both assets.
    
    print("\nIf the weights differ from an equal 33.33% split, the engine behaves correctly.")

if __name__ == "__main__":
    test_hrp()  # Correct function call
