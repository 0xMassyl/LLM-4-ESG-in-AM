import pandas as pd
import numpy as np

def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les rendements logarithmiques de manière robuste.
    Ne supprime pas les lignes s'il manque juste une donnée.
    """
    # 1. Tri par date pour être sûr
    prices = prices.sort_index()
    
    # 2. Remplissage des trous (Forward Fill)
    # Si le prix de mardi manque, on prend celui de lundi.
    prices_filled = prices.ffill()
    
    # 3. Calcul des rendements : ln(P_t / P_{t-1})
    raw_returns = prices_filled / prices_filled.shift(1)
    
    # 4. Nettoyage des infinis (division par 0)
    raw_returns = raw_returns.replace([np.inf, -np.inf], np.nan)
    
    # 5. Logarithme
    log_returns_df = pd.DataFrame(np.log(raw_returns))
    
    # 6. Remplacement des NaN restants par 0.0 (Pas de rendement ce jour-là)
    # C'est la clé pour ne pas avoir une matrice vide !
    log_returns_df = log_returns_df.fillna(0.0)
    
    # On supprime uniquement la toute première ligne (qui est toujours NaN/0 après le shift)
    return log_returns_df.iloc[1:]

def get_covariance_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.cov() * 252

def get_correlation_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.corr()