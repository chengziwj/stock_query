"""CLI entry point for stock query tool."""
from __future__ import annotations

import argparse
import sys
import textwrap

import os

from stock_query.fetcher import fetch_quotes, infer_prefix
from stock_query.formatter import format_quotes
from stock_query.parser import parse_quotes
from stock_query.picker import pick
from stock_query.repl import HistoryStore

_LAST_BATCH_FILE = os.path.expanduser("~/.stock_query_last_batch")


_BASH_COMPLETION = textwrap.dedent("""\
    # stock_query bash completion — source this file in your shell:
    #   eval "$(stock_query shell-completions)"
    # Or add to ~/.bashrc:
    #   source <(stock_query shell-completions)

    _stock_query_complete() {
        local cur prev words cword
        _init_completion || return

        if [[ "$cword" -eq 1 ]]; then
            COMPREPLY=($(compgen -W "query last repl complete shell-completions history" -- "$cur"))
            return
        fi

        if [[ "${words[1]}" == "query" ]]; then
            # Complete stock codes from history
            local codes
            codes=$(stock_query complete "$cur" 2>/dev/null)
            COMPREPLY=($(compgen -W "$codes" -- "$cur"))
        elif [[ "${words[1]}" == "complete" ]]; then
            # Complete the prefix argument from history codes
            local codes
            codes=$(stock_query complete "$cur" 2>/dev/null)
            COMPREPLY=($(compgen -W "$codes" -- "$cur"))
        fi
    }

    complete -F _stock_query_complete stock_query
""")


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

    c = sub.add_parser("complete", help="Output matching stock codes from history for shell completion")
    c.add_argument("prefix", nargs="?", default="", help="Prefix to filter codes (empty = all)")

    s = sub.add_parser("shell-completions", help="Generate shell completion script (bash)")

    h = sub.add_parser("history", help="Interactive history picker (up/down to select, space to mark)")
    h.add_argument("--pick", metavar="N[,N...]", help="Query stocks from history by index (non-interactive)")
    h.add_argument("--rm", metavar="N[,N...]", dest="remove", help="Remove history entries by index")
    h.add_argument("--clear", action="store_true", help="Clear all history")
    h.add_argument("--list", action="store_true", help="List history without interactive picker")

    sub.add_parser("last", help="Re-query the last batch of stocks")
    sub.add_parser("repl", help="Interactive REPL with history tab-completion")
    return parser


def run_query(codes_str: str, save_history: bool = True) -> None:
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

    # Save last batch for quick re-query
    try:
        with open(_LAST_BATCH_FILE, "w") as f:
            for c in codes:
                f.write(c + "\n")
    except OSError:
        pass

    if save_history:
        store = HistoryStore()
        for code, stock in zip(codes, stocks):
            store.add(code, stock.get("name", ""))


def run_complete(prefix: str) -> None:
    """Output matching stock codes from history, one per line."""
    store = HistoryStore()
    entries = store.load()
    prefix_lower = prefix.lower()
    for code, name in entries:
        if code.startswith(prefix) or prefix_lower in name.lower():
            print(code)


def _parse_index_list(raw: str) -> list[int]:
    """Parse comma-separated 1-based indices. Raises ValueError on bad input."""
    indices = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if not part.isdigit():
            raise ValueError(f"Invalid index: {part}")
        indices.append(int(part))
    return indices


def run_history(pick_val: str | None, remove: str | None, clear: bool, list_only: bool) -> None:
    """Manage query history: interactive picker, list, pick, remove, or clear."""
    store = HistoryStore()

    if clear:
        store.clear()
        print("History cleared.")
        return

    if remove:
        try:
            indices = _parse_index_list(remove)
        except ValueError as e:
            print(f"Error: {e}")
            return
        removed = store.remove_by_index(indices)
        if removed:
            for code, name in removed:
                print(f"Removed: {code}  {name}")
        else:
            print("No matching entries found.")
        return

    if pick_val:
        try:
            indices = _parse_index_list(pick_val)
        except ValueError as e:
            print(f"Error: {e}")
            return
        codes = store.get_by_index(indices)
        if not codes:
            print("Error: no matching history entries.")
            return
        run_query(",".join(codes), save_history=False)
        return

    entries = store.load()
    if not entries:
        print("No query history yet.")
        return

    if list_only:
        for i, (code, name) in enumerate(entries, 1):
            label = f"{name}" if name else "-"
            print(f"  {i:>3}. {code:<12} {label}")
        return

    # Default: interactive picker
    selected = pick(entries)
    if selected:
        run_query(",".join(selected), save_history=False)
    else:
        print("Cancelled.")


def run_last() -> None:
    """Re-query the last batch of stocks."""
    try:
        with open(_LAST_BATCH_FILE) as f:
            codes = [line.strip() for line in f if line.strip()]
    except (FileNotFoundError, OSError):
        print("No previous query found.")
        return

    if not codes:
        print("No previous query found.")
        return

    print(f"Re-querying: {', '.join(codes)}")
    run_query(",".join(codes), save_history=False)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "query":
        run_query(args.codes)
    elif args.command == "complete":
        run_complete(args.prefix)
    elif args.command == "shell-completions":
        print(_BASH_COMPLETION)
    elif args.command == "history":
        run_history(args.pick, args.remove, args.clear, args.list)
    elif args.command == "last":
        run_last()
    elif args.command == "repl":
        from stock_query.repl import run_repl
        run_repl()
    else:
        parser.print_help()
        sys.exit(1)
