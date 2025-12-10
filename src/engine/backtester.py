import pandas as pd
import numpy as np
from typing import Dict, Any, cast

def run_backtest(returns: pd.DataFrame, weights: Dict[str, float]) -> pd.DataFrame:
    """
    Simule la performance historique du portefeuille (Base 100).
    """
    # 1. NETTOYAGE STRICT
    returns_clean = returns.apply(pd.to_numeric, errors='coerce').fillna(0.0)
    
    # 2. Alignement des poids
    weights_series = pd.Series(weights).reindex(returns_clean.columns).fillna(0.0)
    
    # 3. Calcul du rendement quotidien pondéré
    portfolio_returns = (returns_clean * weights_series).sum(axis=1)
    
    # 4. Benchmark (1/N)
    benchmark_returns = returns_clean.mean(axis=1)
    
    # 5. Courbes de valeur (Cumulative Return)
    strategy_curve = 100 * (1 + portfolio_returns).cumprod()
    benchmark_curve = 100 * (1 + benchmark_returns).cumprod()
    
    results = pd.DataFrame({
        "Veritas HRP": strategy_curve,
        "Benchmark (1/N)": benchmark_curve
    })
    
    return results

def calculate_metrics(daily_returns: pd.Series) -> Dict[str, Any]:
    """
    Calcule les métriques financières.
    Utilise 'cast' pour forcer les types scalaires de Pandas en float Python.
    """
    # Gestion du cas vide pour satisfaire le retour obligatoire
    if daily_returns.empty:
        return {
            "Total Return": "0.00%",
            "Annual Volatility": "0.00%",
            "Sharpe Ratio": "0.00",
            "Max Drawdown": "0.00%"
        }

    # Nettoyage
    r = pd.to_numeric(daily_returns, errors='coerce').fillna(0.0)

    # --- PERFORMANCE ---
    # cast(float, ...) dit à Pylance d'ignorer le type "Scalar" générique
    total_return_raw = (1 + r).prod()
    total_return = float(cast(float, total_return_raw)) - 1.0

    # --- VOLATILITÉ ANNUALISÉE ---
    std_dev = r.std()
    annual_vol = float(cast(float, std_dev)) * np.sqrt(252)
    
    # --- RATIO DE SHARPE ---
    mean_ret = r.mean()
    mean_ret_ann = float(cast(float, mean_ret)) * 252
    risk_free_rate = 0.02 
    
    if annual_vol == 0:
        sharpe = 0.0
    else:
        sharpe = (mean_ret_ann - risk_free_rate) / annual_vol
    
    # --- MAX DRAWDOWN ---
    cum_ret = (1 + r).cumprod()
    # expanding().max() renvoie une Série ou un Scalar selon le contexte
    peak = cum_ret.expanding(min_periods=1).max()
    drawdown = (cum_ret / peak) - 1.0
    
    min_dd = drawdown.min()
    max_dd = float(cast(float, min_dd))
    
    return {
        "Total Return": f"{total_return:.2%}",
        "Annual Volatility": f"{annual_vol:.2%}",
        "Sharpe Ratio": f"{sharpe:.2f}",
        "Max Drawdown": f"{max_dd:.2%}"
    }