"""
visualizer.py
-------------
All chart-rendering functions using Matplotlib & Seaborn.
Produces a multi-page dashboard saved as a PNG.
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np

# ──────────────────────────────────────────────
#  Global Style
# ──────────────────────────────────────────────

PALETTE = {
    "bg":       "#0D1117",
    "panel":    "#161B22",
    "border":   "#30363D",
    "text":     "#E6EDF3",
    "muted":    "#8B949E",
    "green":    "#3FB950",
    "red":      "#F85149",
    "blue":     "#58A6FF",
    "orange":   "#FFA657",
    "purple":   "#BC8CFF",
    "yellow":   "#E3B341",
}

TICKER_COLORS = ["#58A6FF", "#3FB950", "#FFA657", "#BC8CFF",
                 "#F85149", "#E3B341", "#79C0FF", "#7EE787"]


def _apply_dark_style():
    plt.rcParams.update({
        "figure.facecolor":  PALETTE["bg"],
        "axes.facecolor":    PALETTE["panel"],
        "axes.edgecolor":    PALETTE["border"],
        "axes.labelcolor":   PALETTE["text"],
        "axes.titlecolor":   PALETTE["text"],
        "xtick.color":       PALETTE["muted"],
        "ytick.color":       PALETTE["muted"],
        "text.color":        PALETTE["text"],
        "grid.color":        PALETTE["border"],
        "grid.linewidth":    0.5,
        "legend.facecolor":  PALETTE["panel"],
        "legend.edgecolor":  PALETTE["border"],
        "font.family":       "monospace",
        "font.size":         9,
    })


# ──────────────────────────────────────────────
#  Page 1 – Single Stock Deep Dive
# ──────────────────────────────────────────────

def plot_single_stock(df: pd.DataFrame, ticker: str,
                      save_path: str = None) -> plt.Figure:
    """
    4-panel deep-dive for one stock:
      1. Price + Bollinger Bands + SMAs
      2. Volume (with SMA overlay)
      3. RSI
      4. MACD
    """
    _apply_dark_style()
    fig = plt.figure(figsize=(16, 12), facecolor=PALETTE["bg"])
    fig.suptitle(f"  {ticker}  —  Technical Analysis Dashboard",
                 fontsize=16, fontweight="bold",
                 color=PALETTE["text"], x=0.05, ha="left")

    gs = gridspec.GridSpec(4, 1, hspace=0.08,
                           height_ratios=[3, 1, 1, 1],
                           top=0.93, bottom=0.07,
                           left=0.07, right=0.97)

    # ── Panel 1: Price ──────────────────────────
    ax1 = fig.add_subplot(gs[0])
    ax1.fill_between(df.index, df["BB_Lower"], df["BB_Upper"],
                     alpha=0.12, color=PALETTE["blue"], label="Bollinger Band")
    ax1.plot(df.index, df["BB_Upper"], color=PALETTE["blue"],
             lw=0.6, alpha=0.5)
    ax1.plot(df.index, df["BB_Lower"], color=PALETTE["blue"],
             lw=0.6, alpha=0.5)
    ax1.plot(df.index, df["BB_Mid"],   color=PALETTE["blue"],
             lw=0.8, alpha=0.7, linestyle="--", label="BB Mid (SMA20)")

    for col, color, label in [
        ("SMA_50",  PALETTE["orange"], "SMA 50"),
        ("SMA_200", PALETTE["purple"], "SMA 200"),
    ]:
        if col in df.columns:
            ax1.plot(df.index, df[col], color=color,
                     lw=1.2, label=label)

    # Colour the close line by positive/negative cumulative return
    close = df["Close"].values
    color_line = PALETTE["green"] if close[-1] >= close[0] else PALETTE["red"]
    ax1.plot(df.index, close, color=color_line, lw=1.8, label="Close")

    ax1.set_ylabel("Price (USD)")
    ax1.legend(loc="upper left", fontsize=8, ncol=3)
    ax1.grid(True, axis="x")
    ax1.xaxis.set_visible(False)
    _style_ax(ax1)

    # ── Panel 2: Volume ─────────────────────────
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    colors = [PALETTE["green"] if c >= o else PALETTE["red"]
              for c, o in zip(df["Close"], df["Open"])]
    ax2.bar(df.index, df["Volume"], color=colors, alpha=0.7, width=1)
    if "Volume_SMA" in df.columns:
        ax2.plot(df.index, df["Volume_SMA"],
                 color=PALETTE["yellow"], lw=1.2, label="Vol SMA 20")
        ax2.legend(loc="upper left", fontsize=8)
    ax2.set_ylabel("Volume")
    ax2.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x/1e6:.0f}M"))
    ax2.xaxis.set_visible(False)
    _style_ax(ax2)

    # ── Panel 3: RSI ────────────────────────────
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.plot(df.index, df["RSI"], color=PALETTE["purple"], lw=1.4)
    ax3.axhline(70, color=PALETTE["red"],   lw=0.8, linestyle="--", alpha=0.7)
    ax3.axhline(30, color=PALETTE["green"], lw=0.8, linestyle="--", alpha=0.7)
    ax3.fill_between(df.index, df["RSI"], 70,
                     where=(df["RSI"] >= 70), alpha=0.2,
                     color=PALETTE["red"],   label="Overbought")
    ax3.fill_between(df.index, df["RSI"], 30,
                     where=(df["RSI"] <= 30), alpha=0.2,
                     color=PALETTE["green"], label="Oversold")
    ax3.set_ylim(0, 100)
    ax3.set_ylabel("RSI (14)")
    ax3.legend(loc="upper left", fontsize=8)
    ax3.xaxis.set_visible(False)
    _style_ax(ax3)

    # ── Panel 4: MACD ───────────────────────────
    ax4 = fig.add_subplot(gs[3], sharex=ax1)
    hist_colors = [PALETTE["green"] if v >= 0 else PALETTE["red"]
                   for v in df["MACD_Hist"]]
    ax4.bar(df.index, df["MACD_Hist"],
            color=hist_colors, alpha=0.7, width=1, label="Histogram")
    ax4.plot(df.index, df["MACD"],        color=PALETTE["blue"],   lw=1.2, label="MACD")
    ax4.plot(df.index, df["MACD_Signal"], color=PALETTE["orange"], lw=1.2, label="Signal")
    ax4.axhline(0, color=PALETTE["muted"], lw=0.5)
    ax4.set_ylabel("MACD")
    ax4.legend(loc="upper left", fontsize=8, ncol=3)
    _style_ax(ax4)

    _add_date_formatter(ax4)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight",
                    facecolor=PALETTE["bg"])
        print(f"  💾 Saved → {save_path}")
    return fig


# ──────────────────────────────────────────────
#  Page 2 – Multi-Stock Overview
# ──────────────────────────────────────────────

def plot_multi_stock_overview(data: dict[str, pd.DataFrame],
                              corr_matrix: pd.DataFrame,
                              save_path: str = None) -> plt.Figure:
    """
    3-panel overview for multiple stocks:
      1. Normalised price performance (rebased to 100)
      2. Rolling 30-day volatility
      3. Correlation heatmap
    """
    _apply_dark_style()
    tickers = list(data.keys())
    n = len(tickers)
    colors = TICKER_COLORS[:n]

    fig = plt.figure(figsize=(18, 13), facecolor=PALETTE["bg"])
    fig.suptitle("  Multi-Stock Market Overview",
                 fontsize=16, fontweight="bold",
                 color=PALETTE["text"], x=0.05, ha="left")

    gs = gridspec.GridSpec(2, 2, hspace=0.35, wspace=0.3,
                           top=0.92, bottom=0.07,
                           left=0.06, right=0.97)

    # ── Panel 1: Normalised Performance ─────────
    ax1 = fig.add_subplot(gs[0, :])   # full width
    for (ticker, df), color in zip(data.items(), colors):
        base = df["Close"].iloc[0]
        norm = df["Close"] / base * 100
        ax1.plot(df.index, norm, color=color, lw=1.8, label=ticker)
    ax1.axhline(100, color=PALETTE["muted"], lw=0.7, linestyle="--")
    ax1.set_ylabel("Normalised Price (Base = 100)")
    ax1.set_title("Relative Performance", pad=6)
    ax1.legend(fontsize=9, ncol=n)
    _style_ax(ax1)
    _add_date_formatter(ax1)

    # ── Panel 2: Rolling Volatility ──────────────
    ax2 = fig.add_subplot(gs[1, 0])
    from analyzer import rolling_volatility
    for (ticker, df), color in zip(data.items(), colors):
        vol = rolling_volatility(df, window=30)
        ax2.plot(df.index, vol, color=color, lw=1.4, label=ticker)
    ax2.set_ylabel("Ann. Volatility (%)")
    ax2.set_title("30-Day Rolling Volatility", pad=6)
    ax2.legend(fontsize=8, ncol=2)
    _style_ax(ax2)
    _add_date_formatter(ax2)

    # ── Panel 3: Correlation Heatmap ─────────────
    ax3 = fig.add_subplot(gs[1, 1])
    mask = np.zeros_like(corr_matrix, dtype=bool)
    mask[np.triu_indices_from(mask, k=1)] = True  # show lower triangle only

    cmap = sns.diverging_palette(220, 10, as_cmap=True)
    sns.heatmap(
        corr_matrix,
        ax=ax3,
        annot=True,
        fmt=".2f",
        cmap=cmap,
        vmin=-1, vmax=1,
        linewidths=0.5,
        linecolor=PALETTE["bg"],
        annot_kws={"size": 8},
        cbar_kws={"shrink": 0.8},
    )
    ax3.set_title("Return Correlation Matrix", pad=6)
    ax3.tick_params(axis="x", rotation=45)
    ax3.tick_params(axis="y", rotation=0)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight",
                    facecolor=PALETTE["bg"])
        print(f"  💾 Saved → {save_path}")
    return fig


# ──────────────────────────────────────────────
#  Page 3 – Returns Distribution
# ──────────────────────────────────────────────

def plot_returns_distribution(data: dict[str, pd.DataFrame],
                               save_path: str = None) -> plt.Figure:
    """Distribution of daily returns + box-plot comparison."""
    _apply_dark_style()
    tickers = list(data.keys())
    n = len(tickers)
    colors = TICKER_COLORS[:n]

    fig, axes = plt.subplots(1, 2, figsize=(16, 6),
                              facecolor=PALETTE["bg"])
    fig.suptitle("  Daily Returns Analysis",
                 fontsize=16, fontweight="bold",
                 color=PALETTE["text"], x=0.05, ha="left")
    fig.subplots_adjust(top=0.88, bottom=0.12,
                        left=0.07, right=0.97, wspace=0.3)

    # KDE Plot
    ax1 = axes[0]
    for (ticker, df), color in zip(data.items(), colors):
        ret = df["Close"].pct_change().dropna() * 100
        ret.plot.kde(ax=ax1, label=ticker, color=color, lw=2)
    ax1.axvline(0, color=PALETTE["muted"], lw=0.8, linestyle="--")
    ax1.set_xlabel("Daily Return (%)")
    ax1.set_ylabel("Density")
    ax1.set_title("Return Distribution (KDE)", pad=6)
    ax1.legend(fontsize=9)
    _style_ax(ax1)

    # Box Plot
    ax2 = axes[1]
    returns_list = [data[t]["Close"].pct_change().dropna() * 100 for t in tickers]
    bp = ax2.boxplot(returns_list, labels=tickers,
                     patch_artist=True,
                     medianprops=dict(color=PALETTE["yellow"], lw=2),
                     whiskerprops=dict(color=PALETTE["muted"]),
                     capprops=dict(color=PALETTE["muted"]),
                     flierprops=dict(marker=".", color=PALETTE["muted"],
                                     markersize=3, alpha=0.4))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax2.axhline(0, color=PALETTE["muted"], lw=0.6, linestyle="--")
    ax2.set_ylabel("Daily Return (%)")
    ax2.set_title("Return Spread Comparison", pad=6)
    ax2.tick_params(axis="x", rotation=30)
    _style_ax(ax2)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight",
                    facecolor=PALETTE["bg"])
        print(f"  💾 Saved → {save_path}")
    return fig


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def _style_ax(ax: plt.Axes):
    ax.set_facecolor(PALETTE["panel"])
    for spine in ax.spines.values():
        spine.set_edgecolor(PALETTE["border"])
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    ax.grid(True, axis="x", linestyle=":",  alpha=0.3)


def _add_date_formatter(ax: plt.Axes):
    import matplotlib.dates as mdates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")
