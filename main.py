"""
main.py
-------
Entry point for the Stock Market Analysis Dashboard.

Usage:
    python main.py                         # Default 6 stocks, 1-year
    python main.py --tickers AAPL TSLA     # Custom tickers
    python main.py --period 6mo            # Custom period
    python main.py --focus NVDA            # Deep-dive on one stock
"""

import argparse
import os
import sys
from tabulate import tabulate   # pip install tabulate  (optional, graceful fallback)

from data_loader  import fetch_multiple, fetch_stock_data
from analyzer     import (add_moving_averages, add_bollinger_bands,
                          add_rsi, add_macd, add_ema,
                          add_volume_sma, add_daily_returns,
                          add_cumulative_returns, build_correlation_matrix,
                          summary_stats)
from visualizer   import (plot_single_stock,
                          plot_multi_stock_overview,
                          plot_returns_distribution)

# ──────────────────────────────────────────────
#  Config
# ──────────────────────────────────────────────

DEFAULT_TICKERS = ["AAPL", "TSLA", "GOOGL", "MSFT", "NVDA", "AMZN"]
OUTPUT_DIR      = "output"


def prepare_single(df):
    """Add all indicators needed for the single-stock deep-dive."""
    df = add_moving_averages(df, [20, 50, 200])
    df = add_ema(df, 20)
    df = add_bollinger_bands(df)
    df = add_rsi(df)
    df = add_macd(df)
    df = add_volume_sma(df)
    df = add_daily_returns(df)
    df = add_cumulative_returns(df)
    return df


def print_summary_table(data):
    """Pretty-print summary stats for all tickers."""
    rows = [summary_stats(df, ticker) for ticker, df in data.items()]
    print("\n" + "═" * 70)
    print("  📊  PORTFOLIO SUMMARY")
    print("═" * 70)
    try:
        headers = list(rows[0].keys())
        table   = [[r[h] for h in headers] for r in rows]
        print(tabulate(table, headers=headers, tablefmt="rounded_grid"))
    except ImportError:
        # Graceful fallback without tabulate
        for r in rows:
            print(r)
    print("═" * 70 + "\n")


# ──────────────────────────────────────────────
#  Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="📈 Stock Market Analysis Dashboard")
    parser.add_argument("--tickers", nargs="+", default=DEFAULT_TICKERS,
                        help="Space-separated stock tickers")
    parser.add_argument("--period",  default="1y",
                        choices=["1mo","3mo","6mo","1y","2y"],
                        help="Data period (default: 1y)")
    parser.add_argument("--focus",   default=None,
                        help="Single ticker for deep-dive (default: first ticker)")
    args = parser.parse_args()

    tickers    = [t.upper() for t in args.tickers]
    period     = args.period
    focus      = (args.focus or tickers[0]).upper()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 1. Load Data ──────────────────────────
    raw_data = fetch_multiple(tickers, period)

    # ── 2. Add Indicators to All Stocks ───────
    print("\n🔧 Computing technical indicators...")
    processed = {t: prepare_single(df) for t, df in raw_data.items()}

    # ── 3. Summary Table ──────────────────────
    print_summary_table(processed)

    # ── 4. Correlation Matrix ─────────────────
    corr = build_correlation_matrix(processed)

    # ── 5. Charts ─────────────────────────────
    print("🎨 Rendering charts...\n")

    # Deep-dive on focus stock
    focus_df   = processed[focus]
    path1 = f"{OUTPUT_DIR}/{focus}_technical.png"
    plot_single_stock(focus_df, focus, save_path=path1)

    # Multi-stock overview
    path2 = f"{OUTPUT_DIR}/multi_stock_overview.png"
    plot_multi_stock_overview(processed, corr, save_path=path2)

    # Returns distribution
    path3 = f"{OUTPUT_DIR}/returns_distribution.png"
    plot_returns_distribution(processed, save_path=path3)

    print(f"\n✅  All done! Charts saved in → ./{OUTPUT_DIR}/")
    print("   Open the PNG files to view your dashboard.\n")


if __name__ == "__main__":
    main()
