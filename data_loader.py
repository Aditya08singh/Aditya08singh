"""
data_loader.py
--------------
Handles fetching real stock data via yfinance,
or generating realistic sample data when offline.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def fetch_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Try to fetch real stock data using yfinance.
    Falls back to generated sample data if unavailable.

    Args:
        ticker: Stock symbol (e.g. 'AAPL', 'TSLA')
        period: Period string like '1y', '6mo', '3mo'

    Returns:
        DataFrame with OHLCV columns + ticker column
    """
    try:
        import yfinance as yf
        df = yf.download(ticker, period=period, progress=False)
        if df.empty:
            raise ValueError("Empty data returned")
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        df["Ticker"] = ticker
        print(f"  ✅ Fetched real data for {ticker}")
        return df
    except Exception as e:
        print(f"  ⚠️  yfinance unavailable ({e}). Using generated sample data for {ticker}.")
        return _generate_sample_data(ticker, period)


def fetch_multiple(tickers: list[str], period: str = "1y") -> dict[str, pd.DataFrame]:
    """
    Fetch data for multiple tickers.

    Returns:
        Dict mapping ticker → DataFrame
    """
    print(f"\n📥 Loading data for: {', '.join(tickers)}")
    return {t: fetch_stock_data(t, period) for t in tickers}


# ──────────────────────────────────────────────
# Sample data generator (no internet required)
# ──────────────────────────────────────────────

_BASE_PRICES = {
    "AAPL": 170, "TSLA": 250, "GOOGL": 140,
    "MSFT": 380, "AMZN": 185, "NVDA": 800,
    "META": 500, "NFLX": 600,
}

def _generate_sample_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Simulate realistic OHLCV data using geometric Brownian motion."""
    days_map = {"1mo": 22, "3mo": 66, "6mo": 132, "1y": 252, "2y": 504}
    n_days = days_map.get(period, 252)

    seed = sum(ord(c) for c in ticker)
    rng = np.random.default_rng(seed)

    base = _BASE_PRICES.get(ticker, 100 + rng.integers(0, 400))
    mu = 0.0003          # daily drift
    sigma = 0.018        # daily volatility

    returns = rng.normal(mu, sigma, n_days)
    prices = base * np.exp(np.cumsum(returns))

    high  = prices * (1 + rng.uniform(0.002, 0.015, n_days))
    low   = prices * (1 - rng.uniform(0.002, 0.015, n_days))
    open_ = low + rng.uniform(0, 1, n_days) * (high - low)

    volume = rng.integers(10_000_000, 80_000_000, n_days).astype(float)

    end_date = datetime.today()
    dates = pd.bdate_range(end=end_date, periods=n_days)

    df = pd.DataFrame({
        "Open":   open_,
        "High":   high,
        "Low":    low,
        "Close":  prices,
        "Volume": volume,
        "Ticker": ticker,
    }, index=dates)
    df.index.name = "Date"
    return df
