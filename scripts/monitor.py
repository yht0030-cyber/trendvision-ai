"""
监控脚本 — 定期检查合约信号，输出简明结论
用法:
  python monitor.py           ← 检查 BTC + XAUUSD
  python monitor.py BTC       ← 只检查 BTC
  python monitor.py --loop    ← 持续监控模式（每30分钟）
"""

import sys
import os
import json
import time
from datetime import datetime

# 确保能引用同目录的 trend_analyzer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trend_analyzer import analyze

SUPPORTED_SYMBOLS = ["BTC", "XAUUSD", "ETH"]


def quick_check(symbol: str) -> dict:
    """跑一次完整分析，提取关键信号"""
    try:
        r1h = analyze(symbol, "1h")
        r4h = analyze(symbol, "4h")
    except Exception as e:
        return {"symbol": symbol, "error": str(e), "signal": None}

    # 评分
    sig_1h = r1h.get("signal", {})
    sig_4h = r4h.get("signal", {})

    # 方向
    trend = r1h.get("trend", "unknown")
    trend_4h = r4h.get("trend", "unknown")

    # 价格
    price = r1h.get("current_price", 0)

    # 关键价位
    pivot = r1h.get("pivot_a", {})
    tl_result = r1h.get("trendline", {})
    ch_result = r1h.get("channel", {})

    # 提取关键价位
    key_levels = {}
    if pivot and "pivot_a" in pivot:
        key_levels["分界点A"] = pivot["pivot_a"]["price"]

    # 止损建议（基于前低/前高）
    swings = r1h.get("swings", r1h.get("_candles", []))
    stop_loss = None
    take_profit = None
    if swings:
        if isinstance(swings, list) and len(swings) >= 2 and isinstance(swings[0], dict):
            if "low" in swings[0] and "high" in swings[0]:
                if trend == "up":
                    stop_loss = swings[-1]["low"]
                elif trend == "down":
                    stop_loss = swings[-1]["high"]

    return {
        "symbol": symbol,
        "price": price,
        "trend_1h": trend,
        "trend_4h": trend_4h,
        "long_score": sig_1h.get("long_score", 0),
        "short_score": sig_1h.get("short_score", 0),
        "max_score": sig_1h.get("max_score", 10),
        "key_levels": key_levels,
        "stop_loss": stop_loss,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def print_summary(result: dict):
    """简明输出（一屏读完）"""
    s = result["symbol"]
    p = result["price"]
    t1 = result["trend_1h"]
    t4 = result["trend_4h"]
    lo = result["long_score"]
    sh = result["short_score"]
    mx = result["max_score"]

    if result.get("error"):
        print(f"❌ {s}: {result['error']}")
        return

    # 方向判断
    if t1 == "up" and t4 != "down":
        bias = "📈 偏多"
        action = "做多为主"
    elif t1 == "down" and t4 != "up":
        bias = "📉 偏空"
        action = "做空为主"
    elif t4 == "up" and t1 != "down":
        bias = "📈 4H偏多"
        action = "观望 / 等1H信号共振"
    elif t4 == "down" and t1 != "up":
        bias = "📉 4H偏空"
        action = "观望 / 等1H信号共振"
    else:
        bias = "📊 震荡"
        action = "观望"

    print(f"\n{'='*50}")
    print(f"  {s} @ {p:.2f}  ({result['timestamp']})")
    print(f"{'='*50}")
    print(f"  方向: 1H={t1}  4H={t4}  → {bias}")
    print(f"  评分: 多 {lo}/{mx}  空 {sh}/{mx}", end="")
    if lo >= 5 or sh >= 5:
        print("  ✅ 触发门槛")
    else:
        print("  ⏳ 未触发")
    print(f"  建议: {action}")

    if result["key_levels"]:
        for name, val in result["key_levels"].items():
            dist = abs(val - p)
            print(f"  🎯 {name}: {val:.2f} (距当前 {dist:.2f})")

    if result["stop_loss"]:
        if bias == "📈 偏多":
            print(f"  🛑 止损参考: {result['stop_loss']:.2f}")
        elif bias == "📉 偏空":
            print(f"  🛑 止损参考: {result['stop_loss']:.2f}")

    print(f"{'='*50}\n")


def loop_mode(interval_minutes=60):
    """持续监控模式"""
    print(f"🔄 监控启动（每 {interval_minutes} 分钟检查一次）")
    print(f"按 Ctrl+C 停止\n")
    while True:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] 检查中...")
        for sym in SUPPORTED_SYMBOLS:
            try:
                result = quick_check(sym)
                print_summary(result)
            except Exception as e:
                print(f"  {sym}: 出错 {e}")
        print(f"⏳ 等待 {interval_minutes} 分钟...")
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    if "--loop" in sys.argv:
        loop_mode()
    elif len(sys.argv) > 1 and sys.argv[1].upper() in SUPPORTED_SYMBOLS:
        result = quick_check(sys.argv[1].upper())
        print_summary(result)
    else:
        for sym in SUPPORTED_SYMBOLS:
            result = quick_check(sym)
            print_summary(result)
