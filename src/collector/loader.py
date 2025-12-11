import yfinance as yf  # type: ignore
import pandas as pd
from typing import List, Optional, cast
from datetime import datetime

class MarketDataLoader:
    """
    Service responsible for fetching historical market data from Yahoo Finance.
    Ensures consistent formatting, safe defaults, and normalized outputs
    (Series -> DataFrame) for downstream processing.
    """

    def __init__(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        # Standardizes tickers (uppercased and stripped).
        self.tickers = [t.strip().upper() for t in tickers]

        # Applies default dates when none are provided.
        self.start_date = start_date or "2023-01-01"
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")

        self.raw_prices: pd.DataFrame = pd.DataFrame()

    def fetch_data(self) -> pd.DataFrame:
        """
        Downloads adjusted historical prices and returns a cleaned DataFrame.
        Handles both Series (single ticker) and DataFrame (multiple tickers).
        """
        if not self.tickers:
            raise ValueError("Ticker list is empty.")

        print(f"[Loader] Downloading data from {self.start_date} to {self.end_date} for: {self.tickers}...")

        try:
            # Fetches historical data, automatically adjusted for splits and dividends.
            data = yf.download(
                self.tickers,
                start=self.start_date,
                end=self.end_date,
                progress=False,
                auto_adjust=True
            )

            if data is None or data.empty:
                print("[Loader] No data returned by Yahoo Finance.")
                return pd.DataFrame()

            # Extracts the closing price layer. Falls back to adjusted close if needed.
            if "Close" in data:
                prices_temp = data["Close"]
            elif "Adj Close" in data:
                prices_temp = data["Adj Close"]
            else:
                prices_temp = data

            # Converts Series to DataFrame for consistent structure.
            if isinstance(prices_temp, pd.Series):
                prices = prices_temp.to_frame()
            else:
                prices = cast(pd.DataFrame, prices_temp)

            # Removes rows where all tickers have missing values.
            self.raw_prices = prices.dropna(how="all")

            if self.raw_prices.empty:
                raise ValueError("Data is empty after cleaning.")

            print(f"[Loader] Successfully loaded {len(self.raw_prices)} rows.")
            return self.raw_prices

        except Exception as e:
            # Catches API, connectivity, or formatting errors.
            print(f"[Loader] Critical failure: {e}")
            return pd.DataFrame()
