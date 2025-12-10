import yfinance as yf # type: ignore
import pandas as pd
from typing import List, Optional, cast
from datetime import datetime

class MarketDataLoader:
    """
    Service responsible for fetching financial market data.
    """

    # FIX 1: Utilisation de Optional[str] car la valeur par défaut est None
    def __init__(self, tickers: List[str], start_date: Optional[str] = None, end_date: Optional[str] = None):
        # Nettoyage des tickers (majuscules, espaces)
        self.tickers = [t.strip().upper() for t in tickers]
        
        # Par défaut : De 2023-01-01 à Aujourd'hui (Dynamique)
        if not start_date:
            self.start_date = "2023-01-01"
        else:
            self.start_date = start_date
            
        if not end_date:
            self.end_date = datetime.now().strftime("%Y-%m-%d")
        else:
            self.end_date = end_date

        self.raw_prices: pd.DataFrame = pd.DataFrame()

    def fetch_data(self) -> pd.DataFrame:
        if not self.tickers:
            raise ValueError("Ticker list is empty.")

        print(f"[Loader] Downloading data from {self.start_date} to {self.end_date} for: {self.tickers}...")
        
        try:
            # Téléchargement via yfinance
            data = yf.download(
                self.tickers, 
                start=self.start_date, 
                end=self.end_date, 
                progress=False,
                auto_adjust=True
            )
            
            if data is None or data.empty:
                print("No data received from Yahoo Finance.")
                return pd.DataFrame()

            # Gestion dynamique : Series vs DataFrame
            # Pylance ne sait pas ce que 'prices' va devenir, on utilise une variable intermédiaire
            prices_temp = None

            if 'Close' in data:
                prices_temp = data['Close']
            elif 'Adj Close' in data:
                prices_temp = data['Adj Close']
            else:
                prices_temp = data

            # FIX 2: Conversion forcée en DataFrame si c'est une Series (1 seul ticker)
            if isinstance(prices_temp, pd.Series):
                prices = prices_temp.to_frame()
            else:
                # On cast pour confirmer à Pylance que c'est bien un DataFrame
                prices = cast(pd.DataFrame, prices_temp)

            # Nettoyage
            self.raw_prices = prices.dropna(how='all')
            
            if self.raw_prices.empty:
                raise ValueError("Data is empty after cleaning.")

            print(f"[Loader] Successfully loaded {len(self.raw_prices)} rows.")
            return self.raw_prices

        except Exception as e:
            print(f"[Loader] Critical failure: {e}")
            return pd.DataFrame()