"""Shared query execution pipeline used by both CLI and REPL."""
from __future__ import annotations

import re

from stock_query.fetcher import fetch_quotes, infer_prefix
from stock_query.formatter import format_quotes
from stock_query.namelist import NameList
from stock_query.parser import parse_quotes
from stock_query.store import HistoryStore


def _is_name_like(token: str) -> bool:
    """Heuristic: does this token look like a stock name rather than a code?"""
    # Contains non-ASCII (Chinese) characters → name
    if not token.isascii():
        return True
    # Purely alphabetic and > 5 chars → likely a name (US tickers are ≤5)
    if token.isalpha() and len(token) > 5:
        return True
    return False


def _resolve_codes(raw_tokens: list[str], db_path: str) -> list[str]:
    """Resolve tokens to market-prefixed stock codes.

    - If a token looks like a name, try NameList lookup.
    - Otherwise, use infer_prefix() as before.
    """
    namelist = NameList(db_path)
    resolved = []
    for token in raw_tokens:
        if _is_name_like(token):
            code = namelist.resolve_name(token)
            if code is not None:
                try:
                    resolved.append(infer_prefix(code))
                except ValueError:
                    print(f"Warning: could not determine market for code '{code}'")
                continue
            # Name not found — try as a code anyway (fallback)
            print(f"Warning: '{token}' not found in stock name list, trying as code...")

        try:
            resolved.append(infer_prefix(token))
        except ValueError as e:
            print(f"Warning: {e}")
            continue
    return resolved


def execute_query(codes_str: str, *, save_history: bool = True,
                  store: HistoryStore | None = None) -> None:
    """Run the full query pipeline: split → infer prefixes → fetch → parse → format → persist.

    Supports both stock codes and A-share stock names (e.g. "平安银行 茅台 AAPL").

    Args:
        codes_str: Comma- or space-separated stock codes or names.
        save_history: If True, record each code/name to query history.
        store: Optional HistoryStore instance. Created automatically if not provided.
    """
    tokens = [c.strip() for c in re.split(r"[,\s]+", codes_str) if c.strip()]
    if not tokens:
        print("Usage: provide one or more stock codes/names, separated by spaces or commas.")
        return

    if store is None:
        store = HistoryStore()

    # Resolve names → market-prefixed codes
    full_codes = _resolve_codes(tokens, store.db_path)
    if not full_codes:
        print("Error: no valid stock codes provided.")
        return

    # Fetch
    try:
        raw = fetch_quotes(full_codes)
    except Exception as e:
        print(f"Error: network request failed — {e}")
        return

    if not raw.strip():
        print("Error: received empty response from API.")
        return

    # Parse
    stocks = parse_quotes(raw)
    if not stocks:
        print("Warning: no data returned for the given codes.")
        return

    # Display
    format_quotes(stocks)

    # Persist
    store.save_last_batch(tokens)

    if save_history:
        for token, stock in zip(tokens, stocks):
            store.add(token, stock.get("name", ""))
