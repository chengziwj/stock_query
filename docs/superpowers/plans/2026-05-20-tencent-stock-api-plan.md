# Tencent Stock API CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that queries real-time stock quotes via the Tencent Finance public API with Rich-formatted terminal output.

**Architecture:** Four modules — fetcher (HTTP + prefix inference), parser (response text → structured dicts), formatter (Rich tables/cards), cli (argparse). Data flows: CLI → Fetcher → Parser → Formatter → stdout.

**Tech Stack:** Python 3.10+, requests, rich, pytest

---

### Task 1: Project Scaffold

**Files:**
- Create: `stock_query/__init__.py`
- Create: `stock_query/__main__.py` (placeholder)
- Create: `stock_query/requirements.txt`
- Create: `stock_query/tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```bash
mkdir -p stock_query/tests
```

Write `stock_query/requirements.txt`:
```
requests>=2.28.0
rich>=13.0.0
```

- [ ] **Step 2: Create __init__.py and __main__.py placeholders**

Write `stock_query/__init__.py`:
```python
"""Stock query CLI using Tencent Finance API."""
```

Write `stock_query/__main__.py`:
```python
"""Entry point for python -m stock_query."""
from stock_query.cli import main

main()
```

Write `stock_query/tests/__init__.py`:
```python
```

- [ ] **Step 3: Install dependencies and verify**

```bash
cd /mnt/d/python/stock && pip install -r stock_query/requirements.txt
```

- [ ] **Step 4: Commit**

```bash
git add stock_query/
git commit -m "chore: scaffold stock_query project structure"
```

---

### Task 2: Fetcher Module (with TDD)

**Files:**
- Create: `stock_query/fetcher.py`
- Create: `stock_query/tests/test_fetcher.py`

- [ ] **Step 1: Write the failing test for prefix inference**

Write `stock_query/tests/test_fetcher.py`:
```python
import pytest
from stock_query.fetcher import infer_prefix, fetch_quotes

@pytest.mark.parametrize("code,expected", [
    ("000001", "sz000001"),
    ("002001", "sz002001"),
    ("300001", "sz300001"),
    ("600000", "sh600000"),
    ("601000", "sh601000"),
    ("603000", "sh603000"),
    ("688000", "sh688000"),
    ("00700", "hk00700"),
    ("AAPL", "usAAPL"),
    ("TSLA", "usTSLA"),
])
def test_infer_prefix(code, expected):
    assert infer_prefix(code) == expected

def test_infer_prefix_already_prefixed():
    assert infer_prefix("sz000001") == "sz000001"
    assert infer_prefix("sh600000") == "sh600000"
    assert infer_prefix("hk00700") == "hk00700"
    assert infer_prefix("usAAPL") == "usAAPL"

def test_infer_prefix_empty():
    with pytest.raises(ValueError, match="empty"):
        infer_prefix("")

def test_infer_prefix_unknown():
    with pytest.raises(ValueError, match="Cannot infer"):
        infer_prefix("12345")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_fetcher.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'stock_query.fetcher'`

- [ ] **Step 3: Write fetcher.py with infer_prefix**

Write `stock_query/fetcher.py`:
```python
"""HTTP client for Tencent stock API."""
import re
import requests

TIMEOUT = 10
BASE_URL = "http://qt.gtimg.cn/q="
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finance.qq.com/",
}

SZ_PREFIXES = {"000", "002", "003", "300", "301"}
SH_PREFIXES = {"600", "601", "603", "605", "688", "689"}


def infer_prefix(code: str) -> str:
    """Infer market prefix from stock code pattern."""
    if not code or not code.strip():
        raise ValueError("stock code must not be empty")

    code = code.strip().upper()

    if re.match(r"^(SZ|SH|HK|US)\d", code):
        return code.lower()

    if code[0].isdigit():
        if len(code) == 6:
            prefix = code[:3]
            if prefix in SZ_PREFIXES:
                return f"sz{code}"
            if prefix in SH_PREFIXES:
                return f"sh{code}"
        if len(code) == 5:
            return f"hk{code}"

    if code.isalpha():
        return f"us{code}"

    raise ValueError(f"Cannot infer market prefix for code: {code}")
```

- [ ] **Step 4: Run tests to verify prefix inference passes**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_fetcher.py::test_infer_prefix -v
```
Expected: 11 PASS

- [ ] **Step 5: Add failing test for fetch_quotes with mock**

Append to `stock_query/tests/test_fetcher.py`:
```python
from unittest.mock import patch, Mock

SAMPLE_RESPONSE = (
    'v_sz000001="1~平安银行~000001~10.50~0.10~0.96~10.40~10.60~10.45~10.30~100000~"\n'
    'v_sh600000="1~浦发银行~600000~8.90~-0.05~-0.56~8.95~8.96~9.00~8.85~50000~"\n'
)

def test_fetch_quotes_single():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            text=SAMPLE_RESPONSE,
        )
        result = fetch_quotes(["sz000001"])
        assert "v_sz000001" in result
        mock_get.assert_called_once()
        url = mock_get.call_args[0][0]
        assert "sz000001" in url
        assert url.startswith(BASE_URL)


def test_fetch_quotes_batch():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, text=SAMPLE_RESPONSE)
        result = fetch_quotes(["sz000001", "sh600000"])
        url = mock_get.call_args[0][0]
        assert "sz000001" in url
        assert "sh600000" in url


def test_fetch_quotes_network_error():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.side_effect = requests.ConnectionError("no network")
        with pytest.raises(requests.ConnectionError):
            fetch_quotes(["sz000001"])


def test_fetch_quotes_http_error():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=500, text="error")
        result = fetch_quotes(["sz000001"])
        assert result == ""
```

- [ ] **Step 6: Run tests to verify fail**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_fetcher.py -v -k fetch
```
Expected: FAIL — `fetch_quotes` not defined

- [ ] **Step 7: Implement fetch_quotes**

Append to `stock_query/fetcher.py`:
```python

def fetch_quotes(codes: list[str]) -> str:
    """Fetch real-time quotes from Tencent API.

    Args:
        codes: List of market-prefixed stock codes (e.g. ["sz000001", "sh600000"]).

    Returns:
        Raw response text from the API, or empty string on HTTP error.
    """
    url = BASE_URL + ",".join(codes)

    for attempt in range(2):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.text
            return ""
        except requests.ConnectionError:
            if attempt == 1:
                raise
```

- [ ] **Step 8: Run tests to verify pass**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_fetcher.py -v
```
Expected: all 15 PASS

- [ ] **Step 9: Commit**

```bash
git add stock_query/fetcher.py stock_query/tests/test_fetcher.py
git commit -m "feat: add fetcher module with prefix inference and HTTP client"
```

---

### Task 3: Parser Module (with TDD)

**Files:**
- Create: `stock_query/parser.py`
- Create: `stock_query/tests/test_parser.py`

- [ ] **Step 1: Write the failing test for parse_quotes**

Write `stock_query/tests/test_parser.py`:
```python
import pytest
from stock_query.parser import parse_quotes, get_market

A_SHARE_RESPONSE = (
    'v_sz000001="1~平安银行~000001~10.50~10.40~10.60~100000~5000~'
    '1000~100~200~300~400~500~100~200~300~400~500~200~300~400~500~'
    '100~200~300~400~500~2025-05-20~14:30:00~0.10~0.96~'
    '10.60~10.30~120000~600000~2.50~8.50~0.00~11.44~9.36~'
    '3.00~50000000000~60000000000~1.20~"\n'
)

HK_RESPONSE = (
    'v_hk00700="1~腾讯控股~00700~380.00~375.00~382.00~1000000~'
    '500000000~1.20~385.00~380.00~2025/05/20~14:30:00~'
    '5.00~1.33~4.50~"\n'
)

US_RESPONSE = (
    'v_usAAPL="Apple Inc~AAPL~190.50~1.50~0.79~189.00~191.00~'
    '190.00~188.50~50000000~2025/05/20~14:30:00~"\n'
)

def test_parse_quotes_a_share():
    result = parse_quotes(A_SHARE_RESPONSE)
    assert len(result) == 1
    stock = result[0]
    assert stock["code"] == "000001"
    assert stock["name"] == "平安银行"
    assert stock["price"] == "10.50"

def test_parse_quotes_batch():
    response = A_SHARE_RESPONSE + HK_RESPONSE
    result = parse_quotes(response)
    assert len(result) == 2

def test_parse_quotes_empty():
    result = parse_quotes("")
    assert result == []

def test_parse_quotes_no_match():
    result = parse_quotes("garbage data\nno match here\n")
    assert result == []

def test_get_market():
    assert get_market("sz000001") == "sz"
    assert get_market("sh600000") == "sh"
    assert get_market("hk00700") == "hk"
    assert get_market("usAAPL") == "us"

def test_parse_preserves_all_fields():
    result = parse_quotes(A_SHARE_RESPONSE)
    stock = result[0]
    assert len(stock["_raw"]) > 10  # all raw fields preserved
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_parser.py -v
```
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement parser.py**

Write `stock_query/parser.py`:
```python
"""Parse Tencent stock API response text into structured data."""
import re

# Regex to extract each stock data line
_LINE_RE = re.compile(r'v_(\w+)="([^"]*)"')

# Field indices for A-share market
_A_FIELDS = [
    "market", "name", "code", "price", "prev_close", "open",
    "volume", "bid_volume", "ask_volume",
    "bid1_price", "bid1_vol", "bid2_price", "bid2_vol",
    "bid3_price", "bid3_vol", "bid4_price", "bid4_vol",
    "bid5_price", "bid5_vol",
    "ask1_price", "ask1_vol", "ask2_price", "ask2_vol",
    "ask3_price", "ask3_vol", "ask4_price", "ask4_vol",
    "ask5_price", "ask5_vol",
    "date", "time", "change", "change_pct",
    "high", "low", "volume_total", "amount",
    "turnover", "pe_ratio",
    "_u39", "high_limit", "low_limit",
    "amplitude", "market_cap", "total_market_cap", "pb_ratio",
]

# HK stocks have fewer fields in different order
_HK_FIELDS = [
    "market", "name", "code", "price", "prev_close", "open",
    "volume", "amount", "turnover", "high", "low",
    "date", "time", "change", "change_pct", "pe_ratio",
]

# US stocks
_US_FIELDS = [
    "name", "code", "price", "change", "change_pct",
    "prev_close", "open", "high", "low", "volume",
    "date", "time",
]


def get_market(code: str) -> str:
    """Extract market prefix from a stock code."""
    m = re.match(r"^(sz|sh|hk|us)", code, re.IGNORECASE)
    return m.group(1).lower() if m else ""


def _field_names(market: str, raw_count: int) -> list[str]:
    """Get field name list for a market, padding if needed."""
    if market in ("sz", "sh"):
        fields = list(_A_FIELDS)
    elif market == "hk":
        fields = list(_HK_FIELDS)
    elif market == "us":
        fields = list(_US_FIELDS)
    else:
        fields = []

    # Pad with generic names if raw has more fields than we know
    while len(fields) < raw_count:
        fields.append(f"f{len(fields)}")
    return fields


def parse_quotes(raw_text: str) -> list[dict]:
    """Parse Tencent API response text into a list of stock dicts.

    Each dict contains named fields and a `_raw` key with all raw values.
    """
    results = []
    for m in _LINE_RE.finditer(raw_text):
        vcode = m.group(1)  # e.g. "sz000001"
        raw_values = m.group(2)
        if not raw_values:
            continue
        fields = raw_values.split("~")
        market = get_market(vcode)
        names = _field_names(market, len(fields))
        stock = {names[i]: fields[i] for i in range(len(fields))}
        stock["_raw"] = fields
        results.append(stock)
    return results
```

- [ ] **Step 4: Run tests to verify pass**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_parser.py -v
```
Expected: all 6 PASS

- [ ] **Step 5: Commit**

```bash
git add stock_query/parser.py stock_query/tests/test_parser.py
git commit -m "feat: add parser module for Tencent API response"
```

---

### Task 4: Formatter Module (with TDD)

**Files:**
- Create: `stock_query/formatter.py`
- Create: `stock_query/tests/test_formatter.py`

- [ ] **Step 1: Write the failing test for formatter**

Write `stock_query/tests/test_formatter.py`:
```python
import pytest
from stock_query.formatter import format_quotes, format_value

SINGLE_STOCK = [{
    "code": "000001", "name": "平安银行", "price": "10.50",
    "change": "0.10", "change_pct": "0.96",
    "open": "10.40", "prev_close": "10.40",
    "high": "10.60", "low": "10.30",
    "volume_total": "120000", "amount": "600000",
    "turnover": "2.50", "pe_ratio": "8.50",
    "amplitude": "3.00", "market_cap": "50000000000",
    "_raw": [],
}]

BATCH_STOCKS = [
    SINGLE_STOCK[0],
    {
        "code": "600000", "name": "浦发银行", "price": "8.90",
        "change": "-0.05", "change_pct": "-0.56",
        "open": "8.95", "prev_close": "8.95",
        "high": "9.00", "low": "8.85",
        "volume_total": "80000", "amount": "400000",
        "turnover": "1.80", "pe_ratio": "6.20",
        "amplitude": "1.68", "market_cap": "30000000000",
        "_raw": [],
    },
]


def test_format_value_price():
    assert format_value("price", "10.50") == "10.50"

def test_format_value_change_pct():
    assert format_value("change_pct", "0.96") == "+0.96%"

def test_format_value_volume():
    assert format_value("volume_total", "123456") == "123,456"

def test_format_value_market_cap():
    assert format_value("market_cap", "50000000000") == "50,000,000,000"

def test_format_value_unknown():
    assert format_value("name", "Test") == "Test"

def test_format_quotes_single_does_not_raise():
    # Single stock: renders vertical card (no exception)
    format_quotes(SINGLE_STOCK)

def test_format_quotes_batch_does_not_raise():
    # Batch: renders table (no exception)
    format_quotes(BATCH_STOCKS)

def test_format_quotes_empty():
    # Should not crash on empty
    format_quotes([])
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_formatter.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement formatter.py**

Write `stock_query/formatter.py`:
```python
"""Rich-based output formatting for stock quotes."""
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

NUMERIC_FIELDS = {
    "price", "prev_close", "open", "high", "low",
    "high_limit", "low_limit",
}
VOLUME_FIELDS = {"volume", "volume_total"}
AMOUNT_FIELDS = {"amount", "market_cap", "total_market_cap"}
PCT_FIELDS = {"change_pct", "turnover", "amplitude"}

CARD_FIELDS = [
    ("name", "名称"),
    ("code", "代码"),
    ("price", "最新价"),
    ("change", "涨跌额"),
    ("change_pct", "涨跌幅"),
    ("open", "今开"),
    ("prev_close", "昨收"),
    ("high", "最高"),
    ("low", "最低"),
    ("volume_total", "成交量(手)"),
    ("amount", "成交额(万)"),
    ("turnover", "换手率"),
    ("pe_ratio", "市盈率"),
    ("amplitude", "振幅"),
    ("market_cap", "流通市值"),
]

TABLE_FIELDS = [
    ("name", "名称"),
    ("code", "代码"),
    ("price", "最新价"),
    ("change_pct", "涨跌幅"),
    ("volume_total", "成交量(手)"),
    ("turnover", "换手率"),
    ("pe_ratio", "市盈率"),
]


def format_value(field: str, value: str) -> str:
    """Format a single field value for display."""
    if not value or value == "0" or value == "0.00":
        return "-"

    try:
        if field in NUMERIC_FIELDS:
            return f"{float(value):.2f}"

        if field in PCT_FIELDS:
            v = float(value)
            sign = "+" if v > 0 else ""
            return f"{sign}{v:.2f}%"

        if field in VOLUME_FIELDS or field in AMOUNT_FIELDS:
            v = int(float(value))
            return f"{v:,}"

        if field == "change":
            v = float(value)
            sign = "+" if v > 0 else ""
            return f"{sign}{v:.2f}"

    except (ValueError, TypeError):
        return value

    return value


def _color_for_change(change_str: str) -> str:
    """Return 'red' for positive, 'green' for negative."""
    try:
        v = float(change_str)
        return "red" if v > 0 else "green" if v < 0 else "white"
    except (ValueError, TypeError):
        return "white"


def _render_card(stocks: list[dict]) -> None:
    """Render single stock as a vertical card."""
    stock = stocks[0]
    name = stock.get("name", "?")
    code = stock.get("code", "?")
    console.print(f"\n[bold cyan]{name}[/bold cyan] ({code})", justify="center")
    console.print("─" * 40, style="dim")

    for key, label in CARD_FIELDS:
        raw = stock.get(key, "")
        if key in ("change_pct", "change"):
            color = _color_for_change(raw)
            val = format_value(key, raw)
            console.print(f"  {label}: [{color}]{val}[/{color}]")
        else:
            console.print(f"  {label}: {format_value(key, raw)}")
    console.print()


def _render_table(stocks: list[dict]) -> None:
    """Render multiple stocks as a Rich table."""
    table = Table(box=box.SIMPLE_HEAD, expand=False)
    table.add_column("#", style="dim", width=3)

    for _, label in TABLE_FIELDS:
        justify = "right" if _ != "name" else "left"
        table.add_column(label, justify=justify)

    for i, stock in enumerate(stocks, 1):
        change = stock.get("change_pct", "")
        color = _color_for_change(change)

        row = [str(i)]
        for key, _ in TABLE_FIELDS:
            val = format_value(key, stock.get(key, ""))

            if key in ("change_pct", "change"):
                row.append(f"[{color}]{val}[/{color}]")
            else:
                row.append(val if val else "-")

        table.add_row(*row)

    console.print()
    console.print(table)
    console.print()


def format_quotes(stocks: list[dict]) -> None:
    """Render stock quotes to terminal. Single stock → card, batch → table."""
    if not stocks:
        console.print("[dim]No data to display.[/dim]")
        return

    if len(stocks) == 1:
        _render_card(stocks)
    else:
        _render_table(stocks)
```

- [ ] **Step 4: Run formatter tests**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_formatter.py -v
```
Expected: all 8 PASS

- [ ] **Step 5: Commit**

```bash
git add stock_query/formatter.py stock_query/tests/test_formatter.py
git commit -m "feat: add Rich-based formatter module"
```

---

### Task 5: CLI Module (with TDD)

**Files:**
- Create: `stock_query/cli.py`
- Modify: `stock_query/__main__.py`
- Create: `stock_query/tests/test_cli.py`

- [ ] **Step 1: Write failing test for CLI**

Write `stock_query/tests/test_cli.py`:
```python
import pytest
from unittest.mock import patch, Mock
from stock_query.cli import build_parser, run_query

SAMPLE_RAW = (
    'v_sz000001="1~平安银行~000001~10.50~10.40~10.60~100000~'
    '5000~1000~100~200~300~400~500~100~200~300~400~500~'
    '200~300~400~500~100~200~300~400~500~2025-05-20~14:30:00~'
    '0.10~0.96~10.60~10.30~120000~600000~2.50~8.50~'
    '0.00~11.44~9.36~3.00~50000000000~60000000000~1.20~"\n'
)


def test_build_parser():
    parser = build_parser()
    args = parser.parse_args(["query", "000001,600000"])
    assert args.codes == "000001,600000"


def test_run_query_single(capsys):
    with patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.return_value = SAMPLE_RAW
        run_query("000001")
    captured = capsys.readouterr()
    assert "平安银行" in captured.out


def test_run_query_batch(capsys):
    with patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.return_value = SAMPLE_RAW
        run_query("000001,600000")
    captured = capsys.readouterr()
    assert "平安银行" in captured.out


def test_run_query_network_error(capsys):
    import requests
    with patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.side_effect = requests.ConnectionError("no net")
        run_query("000001")
    captured = capsys.readouterr()
    assert "error" in captured.out.lower() or "Error" in captured.out


def test_main_function(capsys):
    import sys
    with patch.object(sys, "argv", ["stock_query", "query", "000001"]):
        with patch("stock_query.cli.fetch_quotes", return_value=SAMPLE_RAW):
            from stock_query.cli import main
            main()
    captured = capsys.readouterr()
    assert "平安银行" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_cli.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement cli.py**

Write `stock_query/cli.py`:
```python
"""CLI entry point for stock query tool."""
import argparse
import sys

from stock_query.fetcher import fetch_quotes, infer_prefix
from stock_query.parser import parse_quotes
from stock_query.formatter import format_quotes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock_query",
        description="Query real-time stock quotes via Tencent API.",
    )
    sub = parser.add_subparsers(dest="command")

    q = sub.add_parser("query", help="Query stock quotes")
    q.add_argument(
        "codes",
        help="Stock code(s), comma-separated. E.g. 000001,600000,AAPL",
    )
    return parser


def run_query(codes_str: str) -> None:
    """Run a query from raw comma-separated codes string."""
    codes = [c.strip() for c in codes_str.split(",") if c.strip()]
    if not codes:
        print("Usage: stock_query query <code>[,<code>...]")
        return

    # Infer prefixes
    full_codes = []
    for c in codes:
        try:
            full_codes.append(infer_prefix(c))
        except ValueError as e:
            print(f"Warning: {e}")
            continue

    if not full_codes:
        print("Error: no valid stock codes provided.")
        return

    try:
        raw = fetch_quotes(full_codes)
    except Exception as e:
        print(f"Error: network request failed — {e}")
        return

    if not raw.strip():
        print("Error: received empty response from API.")
        return

    stocks = parse_quotes(raw)

    if not stocks:
        print("Warning: no data returned for the given codes.")
        return

    format_quotes(stocks)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "query":
        run_query(args.codes)
    else:
        parser.print_help()
        sys.exit(1)
```

Update `stock_query/__main__.py`:
```python
"""Entry point for python -m stock_query."""
from stock_query.cli import main

main()
```

- [ ] **Step 4: Run CLI tests**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_cli.py -v
```
Expected: all 5 PASS

- [ ] **Step 5: Smoke test with real API**

```bash
cd /mnt/d/python/stock && python -m stock_query query 000001
```
Expected: Rich-formatted card for 平安银行 with real data.

- [ ] **Step 6: Commit**

```bash
git add stock_query/cli.py stock_query/__main__.py stock_query/tests/test_cli.py
git commit -m "feat: add CLI module with query subcommand"
```

---

### Task 6: Integration Test

**Files:**
- Create: `stock_query/tests/test_integration.py`

- [ ] **Step 1: Write integration test**

Write `stock_query/tests/test_integration.py`:
```python
"""Integration test with real Tencent API."""
import pytest
from stock_query.fetcher import fetch_quotes, infer_prefix
from stock_query.parser import parse_quotes
from stock_query.formatter import format_quotes


@pytest.mark.integration
def test_end_to_end_single():
    codes = [infer_prefix("000001")]
    raw = fetch_quotes(codes)
    assert raw, "should get non-empty response"
    stocks = parse_quotes(raw)
    assert len(stocks) == 1
    assert stocks[0]["name"], "should have a name"
    assert stocks[0]["code"] == "000001"


@pytest.mark.integration
def test_end_to_end_batch():
    codes = [infer_prefix("000001"), infer_prefix("600000")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    assert len(stocks) == 2


@pytest.mark.integration
def test_end_to_end_hk():
    codes = [infer_prefix("00700")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    assert len(stocks) == 1


@pytest.mark.integration
def test_end_to_end_us():
    codes = [infer_prefix("AAPL")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    assert len(stocks) == 1


@pytest.mark.integration
def test_format_output_no_crash():
    codes = [infer_prefix("000001")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    # Should not raise
    format_quotes(stocks)
```

- [ ] **Step 2: Run integration tests**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/test_integration.py -v -m integration
```

- [ ] **Step 3: Run all tests**

```bash
cd /mnt/d/python/stock && python -m pytest stock_query/tests/ -v
```
Expected: all unit tests + integration tests PASS

- [ ] **Step 4: Commit**

```bash
git add stock_query/tests/test_integration.py
git commit -m "test: add integration tests with real Tencent API"
```
