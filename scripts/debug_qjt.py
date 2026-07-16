"""
Qjt 区间可视化调试工具
用文字画图展示当前代码检测到的区间，帮你确认 bug 在哪

用法:
  python debug_qjt.py BTC       ← 看 BTC 的 Qjt 区间
  python debug_qjt.py XAUUSD    ← 看黄金
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from trend_analyzer import analyze, find_swings

def print_qjt_visual(symbol: str):
    result = analyze(symbol, "1h")
    qjt = result.get("qjt", {})
    hi = qjt.get("high_intervals", [])
    li = qjt.get("low_intervals", [])
    candles = result.get("_candles", [])
    price = result.get("current_price", 0)

    print(f"\n{'='*60}")
    print(f"  {symbol} 1H — Qjt 区间检测结果")
    print(f"  当前价: {price:.2f}")
    print(f"  K线数: {len(candles)}")
    print(f"{'='*60}\n")

    # ── 上升区间 ──
    print("【检测到的上升区间】(摆动高点→更高摆动高点)")
    if hi:
        print(f"  {'编号':<6}{'起点K':<8}{'终点K':<8}{'跨度':<8}{'起点价':<12}{'终点价':<12}")
        print(f"  {'-'*54}")
        for i, h in enumerate(hi):
            print(f"  Q↑{i+1:<3}  {h['idx']:<8}{h['broken_idx']:<8}{h['qjt']:<8}{h['price']:<12.2f}{candles[h['broken_idx']]['high']:<12.2f}")
    else:
        print("  (无)")

    print()

    # ── 下降区间 ──
    print("【检测到的下降区间】(摆动低点→更低摆动低点)")
    if li:
        print(f"  {'编号':<6}{'起点K':<8}{'终点K':<8}{'跨度':<8}{'起点价':<12}{'终点价':<12}")
        print(f"  {'-'*54}")
        for i, l in enumerate(li):
            print(f"  Q↓{i+1:<3}  {l['idx']:<8}{l['broken_idx']:<8}{l['qjt']:<8}{l['price']:<12.2f}{candles[l['broken_idx']]['low']:<12.2f}")
    else:
        print("  (无)")

    print()

    # ── 趋势结构分析 ──
    print("【问题诊断】")

    # 检查1：上升和下降区间是否交替出现
    all_intervals = []
    for h in hi:
        all_intervals.append({"type": "up", "idx": h["idx"], "broken": h["broken_idx"]})
    for l in li:
        all_intervals.append({"type": "down", "idx": l["idx"], "broken": l["broken_idx"]})
    all_intervals.sort(key=lambda x: x["idx"])

    if len(all_intervals) >= 2:
        # 检查类型是否交替
        alt = True
        prev_type = all_intervals[0]["type"]
        for i, iv in enumerate(all_intervals[1:], 1):
            if iv["type"] == prev_type:
                alt = False
                print(f"  ⚠ 连续两个{ '上升' if prev_type == 'up' else '下降' }区间未交替")
                print(f"    → {all_intervals[i-1]['type']}@{all_intervals[i-1]['idx']} 和 {iv['type']}@{iv['idx']} 都是{ '上升' if prev_type == 'up' else '下降' }")
                print(f"    → 中间可能缺了一个下降/上升区间（趋势转向漏检）")
                break
            prev_type = iv["type"]
        if alt:
            print(f"  ✅ 区间类型交替正常")
    else:
        print(f"  ⚠ 区间数量不足（仅{len(all_intervals)}个），趋势结构不完整")

    # 检查2：嵌套去重
    if len(hi) >= 2:
        # 检查是否有上升区间 A→C 包含 A→B（嵌套）
        hi_sorted = sorted(hi, key=lambda x: x["idx"])
        has_nesting = False
        for i in range(len(hi_sorted)):
            for j in range(i + 1, len(hi_sorted)):
                a, b = hi_sorted[i], hi_sorted[j]
                if a["idx"] <= b["idx"] and a["broken_idx"] >= b["broken_idx"]:
                    if not has_nesting:
                        print(f"  ⚠ 发现嵌套区间（外区间包含内区间）：")
                        has_nesting = True
                    print(f"    → 外区间 Q↑...@{a['idx']}-{a['broken_idx']} 包含 内区间 Q↑...@{b['idx']}-{b['broken_idx']}")
        if not has_nesting:
            print(f"  ✅ 上升区间无嵌套问题")

    if len(li) >= 2:
        li_sorted = sorted(li, key=lambda x: x["idx"])
        has_nesting = False
        for i in range(len(li_sorted)):
            for j in range(i + 1, len(li_sorted)):
                a, b = li_sorted[i], li_sorted[j]
                if a["idx"] <= b["idx"] and a["broken_idx"] >= b["broken_idx"]:
                    if not has_nesting:
                        print(f"  ⚠ 发现嵌套区间（外区间包含内区间）：")
                        has_nesting = True
                    print(f"    → 外区间 Q↓...@{a['idx']}-{a['broken_idx']} 包含 内区间 Q↓...@{b['idx']}-{b['broken_idx']}")
        if not has_nesting:
            print(f"  ✅ 下降区间无嵌套问题")

    # 检查3：上升/下降区间数量对比
    print(f"\n  📊 区间统计: {len(hi)}个上升 + {len(li)}个下降 = {len(all_intervals)}个")
    if len(hi) > 0 and len(li) == 0:
        print(f"  ⛔ 只有上升区间无下降区间 → 趋势转向完全漏检！")
    elif len(hi) == 0 and len(li) > 0:
        print(f"  ⛔ 只有下降区间无上升区间 → 趋势转向完全漏检！")

    print()


if __name__ == "__main__":
    symbols = sys.argv[1:] if len(sys.argv) > 1 else ["BTC", "XAUUSD", "ETH"]
    syms = []
    for s in symbols:
        su = s.upper()
        if su in ("BTC", "XAUUSD", "ETH"):
            syms.append(su)

    if not syms:
        syms = ["BTC", "XAUUSD", "ETH"]

    for s in syms:
        print_qjt_visual(s)
