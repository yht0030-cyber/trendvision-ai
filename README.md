# TrendVision AI

> An AI-powered quantitative futures trading analysis system based on trend-following theory
> **OKX AI Genesis Hackathon** · #OKXAI

## 📌 Overview

**TrendVision AI** converts classic technical analysis theory (trend-following theory) into a complete, code-driven quantitative analysis system. With a single command, get AI-powered market analysis: **direction, score, entry range, stop-loss**.

**Core Philosophy: Replace emotion with discipline. Replace impulse with data.**

## 🏆 Why This Matters

Traditional futures trading has three fatal flaws:
1. **No discipline** — trading by emotion, holding losing positions until liquidation
2. **Information overload** — dozens of contradictory indicators
3. **No review** — not knowing why you won or lost

TrendVision AI eliminates emotion with a **quantitative scoring system + hard rule engine**.

## 🔧 System Architecture

\┌──────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│  Gate.io API · Wallstreetcn API · 1H + 4H K-line data   │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│              Technical Analysis Engine                    │
│  Qjt Ranges · Trend Lines · Pivot Lines · Breakpoint A   │
│  RSI · 13 Candle Patterns · Wave Count · ATR             │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│              Signal Scoring Layer                         │
│  10-point scoring · 4H direction filter (hard rule)       │
│  Trend line + Breakpoint A = strongest signal             │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│              Output Layer                                 │
│  monitor.py one-command monitoring                        │
│  Direction · Score · Entry · Stop-loss · Key levels       │
└──────────────────────────────────────────────────────────┘
\
## 📊 Backtest Results

| Symbol | Overall Win Rate | Trend Line | Pivot Line | Breakpoint A |
|--------|:-:|:-:|:-:|:-:|
| **XAUUSD** | **90%** | 67% | **93%** | 71% |
| **BTC** | **81%** | 66% | 81% | **82%** |
| **ETH** | **70%** | 43% | **87%** | 11% |

> Data source: Gate.io / Wallstreetcn real historical K-line data
> After 4H direction filtering: XAUUSD win rate improved from 71% → 90%

## ⭐ Scoring System (10 points)

| Category | Max | Details |
|----------|:---:|---------|
| Basic Timing | 5 | Price position 2 + RSI position 1 + Candle pattern 2 |
| System Tools | 5 | Pivot line break 3 + Point A break 1 + Trend line break 1 |

**Trigger: ≥ 5 points**
**Strongest: Trend line + Point A simultaneous break (+1 bonus)**

## 🚀 Quick Start

\\ash
# Install dependencies
pip install ccxt pandas numpy requests

# Single asset analysis
python scripts/monitor.py BTC

# Full market scan
python scripts/monitor.py

# Continuous monitoring (auto-check every 30 min)
python scripts/monitor.py --loop

# Custom timeframe
python scripts/monitor.py ETH --timeframe 1h
\
## 🛠 Technical Highlights

1. **13 Candle Reversal Patterns**: Engulfing, Doji, Hammer, Shooting Star, Harami, Piercing, Dark Cloud Cover, Morning Star, Evening Star, etc.
   - *Filtered: only valid near key zones or trend/pivot lines*
2. **RSI Divergence Detection**: Bullish/bearish divergences
3. **Qjt Range Analysis**: Ascending/descending range alternation, nested deduplication
4. **Wave Counting**: Impulse 5 waves + corrective 3 waves
5. **Position Sizing**: ATR-based + total risk capital, max 1/10 per trade

## 📁 Project Structure

\trendvision-ai/
├── scripts/
│   ├── monitor.py          # One-command monitoring (entry point)
│   ├── trend_analyzer.py   # Core analysis engine (111KB)
│   ├── backtest.py         # Backtesting framework
│   ├── chart.py            # Chart generation
│   └── trade_log.py        # Trade logging
├── hackathon-okx/
│   ├── index.html          # Product landing page
│   ├── README.md           # Full README for hackathon
│   ├── PPT.md              # Presentation document
│   ├── logo.svg            # Project logo
│   ├── architecture.svg    # Architecture diagram
│   └── ...
├── .factory/
│   └── rules/
│       └── project.md      # 20 trading rules
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
└── README.md               # This file
\
## ⚠️ Disclaimer

This is a **research and analysis tool**, not financial advice. Trading carries significant risk. Always do your own research and never risk more than you can afford to lose.

## 📝 License

MIT

---

**Made with 🧠 for OKX AI Genesis Hackathon** · #OKXAI · TrendVision AI
