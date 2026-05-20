# Tencent Stock API CLI Design

**Date**: 2026-05-20
**Status**: Approved

## Overview

A Python CLI tool to query real-time stock quotes using the Tencent Finance public API (`qt.gtimg.cn`). Supports A-shares (Shanghai/Shenzhen), Hong Kong, and US markets.

## Architecture

```
stock_query/
├── __init__.py
├── fetcher.py       # HTTP client for Tencent API
├── parser.py        # Response parsing with per-market field mapping
├── formatter.py     # Rich-based table/card rendering
├── cli.py           # argparse CLI entry point
└── requirements.txt # requests, rich
```

**Data flow**: CLI → Fetcher (build URL + HTTP request) → Parser (parse raw text) → Formatter (Rich rendering) → stdout

## Modules

### Fetcher (`fetcher.py`)

- `fetch_quotes(codes: list[str]) -> str`
- Input: list of market-prefixed codes (e.g. `["sz000001", "sh600000"]`)
- Builds URL: `http://qt.gtimg.cn/q={code1,code2,...}`
- Status code check, timeout 10s, 1 retry on failure
- Browser-like headers, proper error wrapping (network, HTTP, timeout)
- Prefix inference: `_infer_prefix(code: str) -> str` — maps common code patterns to market prefixes (000xxx/002xxx→sz, 600xxx/601xxx/603xxx→sh, 5-digit→hk, letters→us)

### Parser (`parser.py`)

- `parse_quotes(raw_text: str) -> list[dict]`
- Input: raw response text from the API
- Extracts each `v_{code}="..."` line via regex
- Splits fields by `~`, maps to named keys per market
- Returns all available fields (code, name, price, change, change_pct, open, prev_close, high, low, volume, amount, turnover, pe_ratio, etc.)
- Market prefix determines field order mapping

### Formatter (`formatter.py`)

- `format_quotes(data: list[dict]) -> None`
- Uses `rich.Console`, `rich.table.Table` for batch mode (horizontal table)
- Single stock: vertical card layout (field: value pairs)
- Color coding: red for price up, green for price down
- Number formatting: thousands separator for volume/amount, 2 decimal places for percentages

### CLI (`cli.py`)

- Subcommand: `query CODES` — where CODES is comma-separated stock codes
- Example: `python -m stock_query query 000001,600000,00700`
- `__main__.py` for `python -m stock_query` entry

## Dependencies

- `requests` — HTTP client
- `rich` — Terminal table/color rendering
- No additional dependencies beyond stdlib

## Behavior

| Scenario | Handling |
|---|---|
| Single stock | Vertical card display |
| Batch (2+) | Horizontal Rich table |
| Invalid code / empty response | Warning message for that code, continue with others |
| Network error | Retry once, then error message |
| Empty input | Usage hint |
