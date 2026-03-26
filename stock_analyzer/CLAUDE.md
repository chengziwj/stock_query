# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (uses uv)
cd stock_analyzer
uv venv
uv pip install -r requirements.txt

# Run analysis
.venv\Scripts\python main.py 600519    # Analyze by stock code
.venv\Scripts\python main.py 比亚迪     # Analyze by Chinese name

# Run tests
.venv\Scripts\python -m pytest tests/ -v
```

## Architecture

Data flows through modules in sequence:

```
data_fetcher.py → technical_indicators.py → trend_analyzer.py → support_resistance.py → volume_price.py → price_prediction.py
```

**Module responsibilities:**

| Module | Purpose |
|--------|---------|
| `data_fetcher.py` | Fetch stock data via akshare API. Contains `StockCodeParser` for parsing codes like "000001", "平安银行" |
| `technical_indicators.py` | Calculate 12 indicators: MA, RSI, MACD, KDJ, WR, CCI, DMI, BBI, OBV, ATR, PSY, Bollinger Bands |
| `trend_analyzer.py` | Analyze indicator signals, return bullish/bearish/oscillating trend with reasons |
| `support_resistance.py` | Identify support/resistance levels from swing highs/lows, Fibonacci, volume zones |
| `volume_price.py` | Analyze volume-price patterns (价升量增, 价跌量缩, etc.), money flow, divergences |
| `price_prediction.py` | Generate price predictions using trend strength score (0-100), target prices, confidence levels |
| `console_ui.py` | All output formatting: colored text, box drawing, width calculations for Chinese characters |
| `indicator_guide.py` | Help system with indicator explanations and quick reference card |

**Key data structures:**

- DataFrame from `data_fetcher`: columns `trade_date`, `open`, `high`, `low`, `close`, `vol`
- `indicators` dict: nested dict with keys `ma`, `rsi`, `macd`, `kdj`, `wr`, `cci`, `dmi`, `bbi`, `obv`, `atr`, `psy`, `bollinger`, `volume_ma`
- `latest` dict: scalar values from `get_latest_values()` for display

**Windows encoding:** `main.py` wraps stdout/stderr with UTF-8 `TextIOWrapper` for Chinese character support.

## Dependencies

- `akshare` - Stock data API (no API key required)
- `pandas` / `numpy` - Data manipulation

## Test Data

Tests use `sample_data` fixture in `test_technical_indicators.py` that generates 100 days of simulated OHLCV data with `np.random.seed(42)`.