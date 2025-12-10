from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

# Imports internes
from src.collector.loader import MarketDataLoader
from src.engine.hrp_optimizer import HRPOptimizer
from src.engine.utils import calculate_log_returns
from src.engine.db_manager import get_latest_scores

app = FastAPI(
    title="Veritas Quant Engine",
    description="API for ESG-filtered HRP Portfolio Optimization",
    version="1.0.0"
)

# --- Modèles de Données ---
class OptimizationRequest(BaseModel):
    tickers: List[str]
    start_date: str = "2021-01-01"
    end_date: str = "2024-01-01"
    apply_esg_filter: bool = True
    esg_threshold: float = 50.0

class OptimizationResult(BaseModel):
    weights: Dict[str, float]
    esg_scores: Dict[str, float]
    filtered_out: List[str]

# --- Endpoints ---

@app.get("/")
def health_check():
    return {"status": "active", "module": "Veritas Quant Engine"}

@app.post("/optimize", response_model=OptimizationResult)
def optimize_portfolio(request: OptimizationRequest):
    """
    Endpoint principal : Filtre ESG -> Téléchargement -> Optimisation HRP
    """
    universe = request.tickers
    dropped_tickers = []
    current_scores = {}

    # 1. Filtre ESG
    if request.apply_esg_filter:
        print(f"🔍 Applying ESG Filter (Threshold: {request.esg_threshold})...")
        try:
            db_scores = get_latest_scores()
        except Exception as e:
            print(f"⚠️ Warning: Database unavailable ({e}). Skipping ESG check.")
            db_scores = {}

        valid_universe = []
        
        for t in universe:
            # Score par défaut = 50 (Neutre) si inconnu
            score = db_scores.get(t, 50.0) 
            current_scores[t] = score
            
            if score >= request.esg_threshold:
                valid_universe.append(t)
            else:
                dropped_tickers.append(t)
        
        universe = valid_universe

    # Sécurité : Il faut au moins 2 actifs pour faire un portefeuille
    if len(universe) < 2:
        # Fallback : Si on a trop filtré, on renvoie une erreur propre
        return OptimizationResult(
            weights={},
            esg_scores=current_scores,
            filtered_out=request.tickers # Tout a été rejeté
        )

    # 2. Données de Marché
    try:
        loader = MarketDataLoader(universe, request.start_date, request.end_date)
        prices = loader.fetch_data()
        
        if prices.empty:
             raise HTTPException(status_code=400, detail="No price data found for these tickers.")
             
        returns = calculate_log_returns(prices)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data loading failed: {str(e)}")

    # 3. Optimisation HRP
    try:
        optimizer = HRPOptimizer(returns)
        weights_series = optimizer.optimize()
        weights_dict = weights_series.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HRP Optimization failed: {str(e)}")

    return OptimizationResult(
        weights=weights_dict,
        esg_scores={k: v for k, v in current_scores.items() if k in universe},
        filtered_out=dropped_tickers
    )

# Bloc de lancement pour debugging facile
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)