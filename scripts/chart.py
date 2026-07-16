"""
K线图绘制模块 — 带趋势线、Qjt区间、分界点A标注
"""
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=8))


def candles_to_df(candles):
    """将OHLC列表转为mplfinance需要的DataFrame"""
    data = []
    for c in candles:
        dt = datetime.fromtimestamp(c["ts"], TZ)
        data.append([dt, c["open"], c["high"], c["low"], c["close"]])
    df = pd.DataFrame(data, columns=["Date", "Open", "High", "Low", "Close"])
    df.set_index("Date", inplace=True)
    return df


def plot_qjt_chart(candles, qjt_result, title="BTC 1H Qjt Analysis",
                   save_path="chart.png"):
    """
    绘制K线图，标注Qjt区间、趋势线、分界点A
    """
    df = candles_to_df(candles)
    hi = qjt_result["high_intervals"]
    lo = qjt_result["low_intervals"]

    # ── 颜色方案 ──
    mc = mpf.make_marketcolors(up="#26a69a", down="#ef5350", edge="inherit", wick="inherit", volume="in")
    style = mpf.make_mpf_style(marketcolors=mc, gridstyle=":", y_on_right=False)

    fig, axes = mpf.plot(
        df, type="candle", style=style,
        volume=False,
        figsize=(22, 12),
        title=title,
        returnfig=True,
        datetime_format="%m/%d %H",
        xrotation=30,
        tight_layout=False,
    )

    ax = axes[0]
    n = len(candles)

    # ── 1. 标注 swing highs / lows ──
    for h in hi:
        idx = h["idx"]
        price = h["price"]
        ax.annotate(
            f"Qjt={h['qjt']}", (idx, price),
            textcoords="offset points", xytext=(0, 10),
            fontsize=7, color="#ef5350", ha="center",
            arrowprops=dict(arrowstyle="->", color="#ef5350", lw=0.5),
        )

    # ── 2. 标注 K98-Qjt80 的区间（高亮） ──
    if len(hi) > 0:
        h0 = hi[0]  # Qjt=80
        idx_start = h0["idx"]    # 98
        idx_end = h0["broken_idx"]  # 178
        price_start = h0["price"]   # 63687
        # 画区间范围框
        rect = FancyBboxPatch(
            (idx_start - 0.5, ax.get_ylim()[0]),
            idx_end - idx_start, ax.get_ylim()[1] - ax.get_ylim()[0],
            boxstyle="round,pad=0.02",
            facecolor="#4caf50", edgecolor="#2e7d32",
            alpha=0.08, linewidth=1.5, linestyle="--",
        )
        ax.add_patch(rect)
        mid_x = (idx_start + idx_end) / 2
        ax.annotate(
            "Qjt=80 (>>39 threshold)", (mid_x, price_start),
            textcoords="offset points", xytext=(0, 25),
            fontsize=10, color="#2e7d32", ha="center", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#c8e6c9", alpha=0.9),
        )

    # ── 3. Draw uptrend line ──
    # Find lowest point before K98
    low_before_k98 = min(c["low"] for c in candles[:98])
    low_before_k98_idx = min(
        range(98), key=lambda i: candles[i]["low"]
    )

    # Find lowest point between K98 and K178 (pullback low)
    low_between = min(c["low"] for c in candles[99:179])
    low_between_idx = 99 + min(
        range(80), key=lambda i: candles[99 + i]["low"]
    )

    # Draw line
    ax.plot(
        [low_before_k98_idx, low_between_idx],
        [low_before_k98, low_between],
        color="#4caf50", linewidth=2, linestyle="-",
        label="Uptrend Line (Qjt=80)",
    )

    # Extend trendline to K199
    slope = (low_between - low_before_k98) / (low_between_idx - low_before_k98_idx)
    x_end = n - 1
    y_end = low_before_k98 + slope * (x_end - low_before_k98_idx)
    ax.plot(
        [low_between_idx, x_end],
        [low_between, y_end],
        color="#4caf50", linewidth=2, linestyle="--", alpha=0.5,
    )

    # ── 4. 标注趋势线跌破 ──
    ax.annotate(
        "X TRENDLINE BROKEN", (n - 1, candles[-1]["low"]),
        textcoords="offset points", xytext=(-40, -30),
        fontsize=11, color="#c62828", ha="center", fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#ffcdd2", alpha=0.9),
        arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.5),
    )

    # ── 5. 标注关键价位 ──
    max_hi_price = max(h["price"] for h in hi)
    ax.axhline(y=max_hi_price, color="#ff9800", linestyle=":", linewidth=0.8)
    ax.annotate(
        f"{max_hi_price:.0f}", (n - 1, max_hi_price),
        textcoords="offset points", xytext=(10, 5),
        fontsize=8, color="#e65100",
    )

    # ── 6. 标注分界点A ──
    for h in hi:
        for l in lo:
            if abs(h["idx"] - l["idx"]) < 10 and l["price"] < h["price"]:
                ax.scatter(l["idx"], l["price"], marker="v", s=60,
                           color="#9c27b0", zorder=5, alpha=0.7)
                break

    ax.legend(loc="upper left", fontsize=9)

    ax.set_title(
        f"{title}\nQjt=80 >> 39 (trendline drawable) | Trendline BROKEN -> Delayed Reversal -> 1H DOWN",
        fontsize=12, fontweight="bold",
    )

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Chart saved to: {save_path}")
    return save_path


if __name__ == "__main__":
    import trend_analyzer as ta

    print("Fetching BTC 1H data...")
    candles, _, _ = ta.fetch_data("BTC", "1h")
    qjt = ta.calc_qjt(candles)

    print("Drawing chart...")
    plot_qjt_chart(candles, qjt, title="BTC 1H - Qjt=80 Uptrend Line BROKEN",
                   save_path="btc_1h_chart.png")
    print("Done!")
