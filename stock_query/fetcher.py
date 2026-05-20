"""HTTP client for Tencent stock API."""
from __future__ import annotations

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

    code = code.strip()

    if len(code) >= 3 and code[:2].upper() in ("SZ", "SH", "HK", "US"):
        return code[:2].lower() + code[2:]

    code = code.upper()

    if code[0].isdigit():
        if len(code) == 6:
            prefix = code[:3]
            if prefix in SZ_PREFIXES:
                return f"sz{code}"
            if prefix in SH_PREFIXES:
                return f"sh{code}"
        if len(code) == 5 and code[0] == "0":
            return f"hk{code}"

    if code.isalpha():
        return f"us{code}"

    raise ValueError(f"Cannot infer market prefix for code: {code}")


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
