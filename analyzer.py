"""
analyzer.py
-----------
All analytical computations: moving averages, RSI, Bollinger Bands,
returns, volatility, and correlation matrix.
"""

import pandas as pd
import numpy as np


# ─────────────────────────────────────────────
#  Technical Indicators
# ─────────────────────────────────────────────

def add_moving_averages(df: pd.DataFrame,
                        windows: list[int] = [20, 50, 200]) -> pd.DataFrame:
    """Add Simple Moving Average columns to the DataFrame."""
    df = df.copy()
    for w in windows:
        df[f"SMA_{w}"] = df["Close"].rolling(window=w).mean()
    return df


def add_ema(df: pd.DataFrame, span: int = 20) -> pd.DataFrame:
    """Add Exponential Moving Average column."""
    df = df.copy()
    df[f"EMA_{span}"] = df["Close"].ewm(span=span, adjust=False).mean()
    return df


def add_bollinger_bands(df: pd.DataFrame,
                        window: int = 20,
                        num_std: float = 2.0) -> pd.DataFrame:
    """Add Bollinger Bands: middle, upper, lower bands."""
    df = df.copy()
    rolling = df["Close"].rolling(window=window)
    df["BB_Mid"]   = rolling.mean()
    df["BB_Upper"] = df["BB_Mid"] + num_std * rolling.std()
    df["BB_Lower"] = df["BB_Mid"] - num_std * rolling.std()
    return df


def add_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Add Relative Strength Index (RSI) column."""
    df = df.copy()
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df


def add_macd(df: pd.DataFrame,
             fast: int = 12,
             slow: int = 26,
             signal: int = 9) -> pd.DataFrame:
    """Add MACD line, signal line, and histogram."""
    df = df.copy()
    ema_fast   = df["Close"].ewm(span=fast,   adjust=False).mean()
    ema_slow   = df["Close"].ewm(span=slow,   adjust=False).mean()
    df["MACD"]        = ema_fast - ema_slow
    df["MACD_Signal"] = df["MACD"].ewm(span=signal, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]
    return df


def add_volume_sma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Add volume moving average for volume analysis."""
    df = df.copy()
    df["Volume_SMA"] = df["Volume"].rolling(window=window).mean()
    return df


# ─────────────────────────────────────────────
#  Returns & Volatility
# ─────────────────────────────────────────────

def add_daily_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add daily percentage return column."""
    df = df.copy()
    df["Daily_Return"] = df["Close"].pct_change() * 100
    return df


def add_cumulative_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add cumulative return column (base = 100)."""
    df = df.copy()
    df["Cumulative_Return"] = (1 + df["Close"].pct_change()).cumprod() * 100
    return df


def rolling_volatility(df: pd.DataFrame, window: int = 30) -> pd.Series:
    """Annualised rolling volatility (std of log returns × √252)."""
    log_ret = np.log(df["Close"] / df["Close"].shift(1))
    return log_ret.rolling(window).std() * np.sqrt(252) * 100


# ─────────────────────────────────────────────
#  Multi-Stock Correlation
# ─────────────────────────────────────────────

def build_correlation_matrix(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build a correlation matrix from multiple stock DataFrames.

    Args:
        data: Dict of ticker → DataFrame (must have 'Close' column)

    Returns:
        Correlation DataFrame
    """
    close_prices = pd.DataFrame({
        ticker: df["Close"]
        for ticker, df in data.items()
    })
    returns = close_prices.pct_change().dropna()
    return returns.corr()


# ─────────────────────────────────────────────
#  Summary Statistics
# ─────────────────────────────────────────────

def summary_stats(df: pd.DataFrame, ticker: str = "") -> dict:
    """Return a summary dict for a single stock."""
    close = df["Close"]
    daily_ret = close.pct_change().dropna()

    current = close.iloc[-1]
    start   = close.iloc[0]
    total_return = (current - start) / start * 100

    return {
        "Ticker":          ticker,
        "Current Price":   f"${current:,.2f}",
        "Period Return":   f"{total_return:+.1f}%",
        "52W High":        f"${close.max():,.2f}",
        "52W Low":         f"${close.min():,.2f}",
        "Avg Daily Return":f"{daily_ret.mean()*100:+.3f}%",
        "Volatility (ann)":f"{daily_ret.std()*np.sqrt(252)*100:.1f}%",
        "Sharpe (approx)": f"{(daily_ret.mean()/daily_ret.std())*np.sqrt(252):.2f}",
    }
