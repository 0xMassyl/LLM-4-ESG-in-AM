# -------------------------------------------------
# External dependency used to fetch market data
# Yahoo Finance is used as a free and simple data source
# -------------------------------------------------
import yfinance as yf  # type: ignore

# -------------------------------------------------
# Data handling and typing utilities
# -------------------------------------------------
import pandas as pd
from typing import List, Optional, cast
from datetime import datetime


class MarketDataLoader:
    """
    Class responsible for downloading historical market prices.

    Why this class exists:
    - isolates external data dependency (Yahoo Finance)
    - guarantees consistent DataFrame output
    - protects the rest of the system from API edge cases
    """

    def __init__(
        self,
        tickers: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        # Normalize tickers to avoid duplicates and formatting issues.
        # Example: " aapl " -> "AAPL"
        self.tickers = [t.strip().upper() for t in tickers]

        # Apply default start date if none is provided.
        # This avoids querying an excessively long history by mistake.
        self.start_date = start_date or "2023-01-01"

        # Apply default end date as today's date.
        # Ensures the loader always has a valid end boundary.
        self.end_date = end_date or datetime.now().strftime("%Y-%m-%d")

        # Placeholder to store raw price data after download.
        # This allows debugging or reuse without re-fetching.
        self.raw_prices: pd.DataFrame = pd.DataFrame()

    def fetch_data(self) -> pd.DataFrame:
        """
        Downloads historical price data and returns a clean DataFrame.

        This method:
        - fetches adjusted prices
        - handles single vs multiple tickers
        - removes unusable rows
        - guarantees a DataFrame output
        """

        # Defensive check: downstream logic requires at least one ticker.
        if not self.tickers:
            raise ValueError("Ticker list is empty.")

        # Logging for transparency during execution.
        print(
            f"[Loader] Downloading data from {self.start_date} "
            f"to {self.end_date} for: {self.tickers}..."
        )

        try:
            # Call Yahoo Finance API.
            # auto_adjust=True ensures prices account for splits/dividends.
            data = yf.download(
                self.tickers,
                start=self.start_date,
                end=self.end_date,
                progress=False,
                auto_adjust=True
            )

            # If API returns nothing, exit early.
            if data is None or data.empty:
                print("[Loader] No data returned by Yahoo Finance.")
                return pd.DataFrame()

            # Yahoo Finance returns a multi-index DataFrame.
            # We extract closing prices explicitly.
            if "Close" in data:
                prices_temp = data["Close"]
            elif "Adj Close" in data:
                # Fallback for older formats
                prices_temp = data["Adj Close"]
            else:
                # Last resort: assume returned object is already prices
                prices_temp = data

            # Normalize output:
            # - Single ticker -> Series
            # - Multiple tickers -> DataFrame
            # Convert everything to DataFrame for consistency.
            if isinstance(prices_temp, pd.Series):
                prices = prices_temp.to_frame()
            else:
                prices = cast(pd.DataFrame, prices_temp)

            # Remove rows where all tickers are missing.
            # This avoids propagating NaNs to return calculations.
            self.raw_prices = prices.dropna(how="all")

            # Final safety check.
            # An empty DataFrame would break the optimizer.
            if self.raw_prices.empty:
                raise ValueError("Data is empty after cleaning.")

            print(f"[Loader] Successfully loaded {len(self.raw_prices)} rows.")

            return self.raw_prices

        except Exception as e:
            # Catch all failures:
            # - network issues
            # - Yahoo API changes
            # - unexpected data formats
            print(f"[Loader] Critical failure: {e}")

            # Return empty DataFrame to let caller decide fallback strategy.
            return pd.DataFrame()
