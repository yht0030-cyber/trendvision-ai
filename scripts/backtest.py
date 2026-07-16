"""
回测模块 — 对历史K线逐根跑系统信号，统计准确率

用法:
  python backtest.py BTC 1h 200     # 回测BTC 1H最近200根K线
  python backtest.py XAUUSD 4h 100  # 回测XAUUSD 4H最近100根
  python backtest.py BTC all        # 对所有品种回测并出报告
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trend_analyzer as ta

TZ = timezone(timedelta(hours=8))


def _build_4h_trend_map(candles_1h, candles_4h):
    """为每根1H K线映射其所处的4H趋势方向。
    通过时间戳把1H对齐到最近一根已收盘的4H，再取该4H窗口的趋势。"""
    trend_cache = {}
    ts4 = [c["ts"] for c in candles_4h]
    mapping = []
    for c in candles_1h:
        t = c["ts"]
        # 找到 <= t 的最后一根4H
        idx4 = -1
        for j in range(len(ts4)):
            if ts4[j] <= t:
                idx4 = j
            else:
                break
        if idx4 < 20:
            mapping.append(None)
            continue
        if idx4 not in trend_cache:
            window4 = candles_4h[:idx4 + 1]
            sw4 = ta.find_swings(window4)
            trend_cache[idx4] = ta.count_waves(sw4, len(window4))[1]
        mapping.append(trend_cache[idx4])
    return mapping


def backtest(symbol, timeframe="1h", lookback=200, use_4h_filter=True):
    """
    逐根回测：对每根K线计算系统信号，记录后续N根内的价格走势
    统计信号准确率
    use_4h_filter: 启用4H方向过滤（只统计顺势信号）
    """
    print(f"正在拉取 {symbol} {timeframe} 数据...")
    if symbol.upper() == "XAUUSD":
        candles, preclose, _ = ta.fetch_data(symbol, timeframe)
    else:
        candles, preclose, _ = ta.fetch_data(symbol, timeframe)

    if not candles or len(candles) < 50:
        print(f"数据不足 ({len(candles) if candles else 0}根)")
        return None

    n = len(candles)

    # 4H 方向序列（用于顺势过滤），仅加密货币/黄金支持
    trend4h_at = None
    if use_4h_filter:
        try:
            c4h, _, _ = ta.fetch_data(symbol, "4h")
            trend4h_at = _build_4h_trend_map(candles, c4h)
        except Exception:
            trend4h_at = None

    # 回测参数
    test_start = max(30, n - lookback)  # 至少留30根做初始化
    forward_bars = 12  # 信号发出后12根K线内验证

    results = {
        "symbol": symbol,
        "timeframe": timeframe,
        "total_candles": n,
        "tested_candles": n - test_start,
        "forward_bars": forward_bars,
        "long_signals": [],
        "short_signals": [],
        "long_stats": {"total": 0, "wins": 0, "losses": 0, "neutral": 0},
        "short_stats": {"total": 0, "wins": 0, "losses": 0, "neutral": 0},
    }

    for i in range(test_start, n):
        # 用截至当前的数据做分析
        window = candles[:i + 1]

        # 计算指标
        closes = [c["close"] for c in window]
        atr_vals = ta.calc_atr(window, 14)
        atr14 = atr_vals[-1] if atr_vals else 10

        # 量化信号评分（与实盘共用 ta.score_from_window）
        t4 = trend4h_at[i] if trend4h_at else None
        signal = ta.score_from_window(window, trend_4h=t4)
        if not signal:
            continue

        current = candles[i]["close"]

        # 验证后续走势
        future_high = max(c["high"] for c in candles[i+1:min(i+1+forward_bars, n)]) if i+1 < n else current
        future_low = min(c["low"] for c in candles[i+1:min(i+1+forward_bars, n)]) if i+1 < n else current
        future_close = candles[min(i+forward_bars, n-1)]["close"] if i+forward_bars < n else current

        # 做多信号验证
        if signal["long_trigger"]:
            # 赢: 后续涨超入场价1ATR
            win_threshold = current + atr14 * 0.5 if atr14 else current * 1.005
            loss_threshold = current - atr14 * 0.5 if atr14 else current * 0.995

            if future_high >= win_threshold:
                outcome = "win"
            elif future_low <= loss_threshold:
                outcome = "loss"
            else:
                outcome = "neutral"

            results["long_signals"].append({
                "idx": i,
                "entry": round(current, 2),
                "outcome": outcome,
                "future_high": round(future_high, 2),
                "future_low": round(future_low, 2),
                "score": signal["long_score"],
            })
            results["long_stats"]["total"] += 1
            if outcome == "win":
                results["long_stats"]["wins"] += 1
            elif outcome == "loss":
                results["long_stats"]["losses"] += 1
            else:
                results["long_stats"]["neutral"] += 1

        # 做空信号验证
        if signal["short_trigger"]:
            win_threshold = current - atr14 * 0.5 if atr14 else current * 0.995
            loss_threshold = current + atr14 * 0.5 if atr14 else current * 1.005

            if future_low <= win_threshold:
                outcome = "win"
            elif future_high >= loss_threshold:
                outcome = "loss"
            else:
                outcome = "neutral"

            results["short_signals"].append({
                "idx": i,
                "entry": round(current, 2),
                "outcome": outcome,
                "future_high": round(future_high, 2),
                "future_low": round(future_low, 2),
                "score": signal["short_score"],
            })
            results["short_stats"]["total"] += 1
            if outcome == "win":
                results["short_stats"]["wins"] += 1
            elif outcome == "loss":
                results["short_stats"]["losses"] += 1
            else:
                results["short_stats"]["neutral"] += 1

    return results



def format_backtest(results):
    """格式化回测报告"""
    if not results:
        return "无回测数据"

    sym = results["symbol"]
    tf = results["timeframe"]
    n = results["tested_candles"]
    fwd = results["forward_bars"]

    lines = [
        f"\n═══ {sym} {tf} 回测报告 ═══",
        f"  测试K线: {n} 根 | 前望: {fwd} 根",
        "",
    ]

    for direction, label in [("long", "做多信号"), ("short", "做空信号")]:
        st = results[f"{direction}_stats"]
        total = st["total"]
        if total == 0:
            lines.append(f"  {label}: 无信号触发")
            continue

        wins = st["wins"]
        losses = st["losses"]
        neutral = st["neutral"]
        win_rate = wins / total * 100 if total else 0

        lines.append(f"  {label}: {total} 次 | 胜率 {win_rate:.0f}% "
                     f"({wins}盈/{losses}亏/{neutral}平)")

        # 逐个信号
        sigs = results[f"{direction}_signals"]
        if sigs:
            lines.append(f"    最近5次:")
            for s in sigs[-5:]:
                outcome_icon = {"win": "+", "loss": "-", "neutral": "~"}[s["outcome"]]
                lines.append(f"      {outcome_icon} K{s['idx']} @{s['entry']} 分={s['score']}")

    # 综合
    long_total = results["long_stats"]["total"]
    short_total = results["short_stats"]["total"]
    all_wins = results["long_stats"]["wins"] + results["short_stats"]["wins"]
    all_total = long_total + short_total
    if all_total > 0:
        lines.append(f"\n  综合准确率: {all_wins/all_total*100:.0f}% ({all_wins}/{all_total})")

    return "\n".join(lines)


# ─── 趋势线/拐点线/A点 突破回测 ──────────────────

def backtest_trend_breaks(symbol, timeframe="1h", lookback=200):
    """
    专门回测趋势线/拐点线/分界点A 突破后的走势
    统计突破后反转的准确率
    """
    print(f"正在拉取 {symbol} {timeframe} 数据 (突破回测)...")
    if symbol.upper() == "XAUUSD":
        candles, preclose, _ = ta.fetch_data(symbol, timeframe)
    else:
        candles, preclose, _ = ta.fetch_data(symbol, timeframe)

    if not candles or len(candles) < 60:
        return None

    n = len(candles)
    forward_bars = 24
    test_start = max(40, n - lookback)

    results = {
        "trendline": {"total": 0, "correct": 0},
        "channel": {"total": 0, "correct": 0},
        "pivot_a": {"total": 0, "correct": 0},
    }

    for i in range(test_start, n):
        window = candles[:i + 1]
        current = candles[i]["close"]

        swings = ta.find_swings(window, lookback=3)
        qjt = ta.calc_qjt(window)
        atr_vals = ta.calc_atr(window, 14)
        atr_val = atr_vals[-1] if atr_vals else 0

        tl = ta.find_trendline(window, swings, qjt)
        ch = ta.find_channel(window, swings, qjt)
        pa = ta.find_pivot_a(window, swings, qjt)

        future_high = max(c["high"] for c in candles[i+1:min(i+1+forward_bars, n)]) if i+1 < n else current
        future_low = min(c["low"] for c in candles[i+1:min(i+1+forward_bars, n)]) if i+1 < n else current

        # ATR-based threshold: 0.75x ATR minimum move to confirm reversal
        threshold = atr_val * 0.75

        # 趋势线突破验证
        if tl and tl.get("broken"):
            if tl["type"] == "uptrend":
                correct = (current - future_low) > threshold
            else:
                correct = (future_high - current) > threshold
            results["trendline"]["total"] += 1
            if correct:
                results["trendline"]["correct"] += 1

        # 拐点线突破验证
        if ch and ch.get("broken"):
            if ch["type"] == "uptrend":
                correct = (current - future_low) > threshold
            else:
                correct = (future_high - current) > threshold
            results["channel"]["total"] += 1
            if correct:
                results["channel"]["correct"] += 1

        # 分界点A 突破验证
        if pa and pa.get("main_a"):
            a_price = pa["main_a"]["price"]
            if (pa["main_a"]["type"] == "low" and current < a_price) or \
               (pa["main_a"]["type"] == "high" and current > a_price):
                correct = (current - future_low) > threshold if pa["main_a"]["type"] == "low" else (future_high - current) > threshold
                results["pivot_a"]["total"] += 1
                if correct:
                    results["pivot_a"]["correct"] += 1

    return results


def format_break_backtest(results):
    """格式化突破回测结果"""
    if not results:
        return "无数据"
    lines = ["\n═══ 核心工具突破准确率 ═══"]
    book_expected = {"trendline": 70, "channel": 80, "pivot_a": 78}

    for tool, label in [("trendline", "趋势线"), ("channel", "拐点线"), ("pivot_a", "分界点A")]:
        st = results[tool]
        if st["total"] == 0:
            lines.append(f"  {label}: 无突破事件")
            continue
        acc = st["correct"] / st["total"] * 100
        lines.append(f"  {label}: {st['correct']}/{st['total']} = {acc:.0f}% "
                     f"(书预期 ~{book_expected[tool]}%)")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    symbol = sys.argv[1]

    if symbol.lower() == "all":
        # 全品种回测
        for sym in ["BTC", "XAUUSD", "ETH"]:
            print(f"\n{'='*60}")
            try:
                r = backtest(sym, "1h", 200)
                print(format_backtest(r))
                br = backtest_trend_breaks(sym, "1h", 200)
                print(format_break_backtest(br))
            except Exception as e:
                print(f"  {sym} 回测失败: {e}")
    else:
        tf = sys.argv[2] if len(sys.argv) > 2 else "1h"
        lookback = int(sys.argv[3]) if len(sys.argv) > 3 else 200

        r = backtest(symbol, tf, lookback)
        print(format_backtest(r))

        br = backtest_trend_breaks(symbol, tf, lookback)
        print(format_break_backtest(br))


