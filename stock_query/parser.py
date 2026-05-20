"""Parse Tencent stock API response text into structured data."""
from __future__ import annotations

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
