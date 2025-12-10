from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import numpy as np

# Internal imports
from src.collector.loader import MarketDataLoader
from src.engine.hrp_optimizer import HRPOptimizer
from src.engine.utils import calculate_log_returns
from src.engine.db_manager import get_latest_scores

app = FastAPI(
    title="Veritas Quant Engine",
    description="API for ESG-filtered HRP Portfolio Optimization",
    version="1.0.0"
)

# --------------------------------------------------------------------
# Data Models
# --------------------------------------------------------------------

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


# --------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------

@app.get("/")
def health_check():
    return {"status": "active", "module": "Veritas Quant Engine"}


@app.post("/optimize", response_model=OptimizationResult)
def optimize_portfolio(request: OptimizationRequest):
    """
    Portfolio optimization pipeline:
    1. Optional ESG screening.
    2. Historical data retrieval.
    3. HRP optimization on filtered assets.
    """
    universe = request.tickers
    dropped_tickers = []
    current_scores = {}

    # ------------------------------------------------------------
    # 1. ESG Filter
    # ------------------------------------------------------------
    if request.apply_esg_filter:
        print(f"[ESG] Applying ESG filter (Threshold: {request.esg_threshold})...")
        try:
            db_scores = get_latest_scores()
        except Exception as e:
            print(f"[ESG] Warning: Cannot access ESG database ({e}). Default scores applied.")
            db_scores = {}

        valid_universe = []

        for t in universe:
            # Default score = 50 when missing in the database.
            score = db_scores.get(t, 50.0)
            current_scores[t] = score

            if score >= request.esg_threshold:
                valid_universe.append(t)
            else:
                dropped_tickers.append(t)

        universe = valid_universe

    # Need at least two assets for allocation.
    if len(universe) < 2:
        return OptimizationResult(
            weights={},
            esg_scores=current_scores,
            filtered_out=request.tickers
        )

    # ------------------------------------------------------------
    # 2. Market Data Retrieval
    # ------------------------------------------------------------
    try:
        loader = MarketDataLoader(universe, request.start_date, request.end_date)
        prices = loader.fetch_data()

        if prices.empty:
            raise HTTPException(status_code=400, detail="No price data found for the selected tickers.")

        returns = calculate_log_returns(prices)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data loading failed: {str(e)}")

    # ------------------------------------------------------------
    # 3. HRP Optimization
    # ------------------------------------------------------------
    try:
        optimizer = HRPOptimizer(returns)
        weights_series = optimizer.optimize()
        weights_dict = weights_series.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HRP optimization failed: {str(e)}")

    return OptimizationResult(
        weights=weights_dict,
        esg_scores={k: v for k, v in current_scores.items() if k in universe},
        filtered_out=dropped_tickers
    )


# Local run helper
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
