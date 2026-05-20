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
