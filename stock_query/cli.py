"""CLI entry point for stock query tool."""
from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
import time
from datetime import datetime

from stock_query.fetcher import infer_prefix
from stock_query.picker import pick
from stock_query.query import execute_query
from stock_query.store import HistoryStore


def _get_bash_completion() -> str:
    """Return the bash completion script, computed lazily."""
    return textwrap.dedent("""\
    # stock_query bash completion — source this file in your shell:
    #   eval "$(stock_query shell-completions)"
    # Or add to ~/.bashrc:
    #   source <(stock_query shell-completions)

    _stock_query_complete() {
        local cur prev words cword
        _init_completion || return

        if [[ "$cword" -eq 1 ]]; then
            COMPREPLY=($(compgen -W "query last watchlist repl complete shell-completions history refresh-namelist" -- "$cur"))
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


def _parse_duration(raw: str) -> int:
    """Parse a duration string like '10s', '5m', '1h' into seconds."""
    m = re.match(r"^(\d+)\s*(s|m|h)?$", raw.strip())
    if not m:
        raise ValueError(f"Invalid duration: {raw}")
    value = int(m.group(1))
    unit = m.group(2) or "s"
    if unit == "m":
        return value * 60
    elif unit == "h":
        return value * 3600
    return value


def _fmt_interval(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}m{s}s" if m > 0 else f"{s}s"


def _watch_loop(codes_str: str, interval: int) -> None:
    """Run a query repeatedly with the given interval in seconds."""
    interval_label = _fmt_interval(interval)
    try:
        while True:
            os.system("clear" if os.name == "posix" else "cls")

            # Header placeholder — countdown slot will be updated in-place
            now = datetime.now().strftime("%H:%M:%S")
            print(f"\033[1mAuto-refresh every {interval_label}  |  {now}  |  Ctrl+C to stop\033[0m")
            print()

            run_query(codes_str, save_history=False)

            # Countdown: jump to header line and update in place
            for remaining in range(interval, 0, -1):
                label = _fmt_interval(remaining)
                status = f"\033[1mAuto-refresh every {interval_label}  |  Next in {label}  |  {datetime.now().strftime('%H:%M:%S')}  |  Ctrl+C to stop\033[0m"
                print(f"\033[H{status}\033[K", end="")
                sys.stdout.flush()
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopped.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stock_query",
        description="Query real-time stock quotes via Tencent API.",
    )
    sub = parser.add_subparsers(dest="command")

    q = sub.add_parser("query", help="Query stock quotes by code or name")
    q.add_argument(
        "codes",
        nargs="+",
        help="Stock code(s) or name(s), separated by spaces. E.g. 000001 平安银行 AAPL",
    )
    q.add_argument("--watch", metavar="N[s|m|h]", help="Auto-refresh interval, e.g. 10s, 5m, 1h")

    c = sub.add_parser("complete", help="Output matching stock codes from history for shell completion")
    c.add_argument("prefix", nargs="?", default="", help="Prefix to filter codes (empty = all)")

    s = sub.add_parser("shell-completions", help="Generate shell completion script (bash)")

    h = sub.add_parser("history", help="Interactive history picker (up/down to select, space to mark)")
    h.add_argument("--pick", metavar="N[,N...]", help="Query stocks from history by index (non-interactive)")
    h.add_argument("--rm", metavar="N[,N...]", dest="remove", help="Remove history entries by index")
    h.add_argument("--clear", action="store_true", help="Clear all history")
    h.add_argument("--list", action="store_true", help="List history without interactive picker")

    l = sub.add_parser("last", help="Re-query the last batch of stocks")
    l.add_argument("--watch", metavar="N[s|m|h]", help="Auto-refresh interval, e.g. 10s, 5m, 1h")

    wl = sub.add_parser("watchlist", help="Manage watchlist (favorites)")
    wl.add_argument("action", nargs="?", choices=["add", "rm"], help="add or remove stocks")
    wl.add_argument("codes", nargs="?", help="Stock code(s), comma-separated")
    wl.add_argument("--clear", action="store_true", help="Clear entire watchlist")
    wl.add_argument("--list", action="store_true", help="List watchlist without interactive picker")

    sub.add_parser("repl", help="Interactive REPL with history tab-completion")

    nl = sub.add_parser("refresh-namelist", help="Download/refresh the A-share stock name list for name-based lookup")
    nl.add_argument("--force", action="store_true", help="Force re-download even within cooldown period")
    return parser


def run_query(codes_str: str, save_history: bool = True) -> None:
    """Run a query from raw comma-separated codes string."""
    execute_query(codes_str, save_history=save_history)


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


def run_last(watch: str | None = None) -> None:
    """Re-query the last batch of stocks.

    Args:
        watch: Optional auto-refresh interval string (e.g. "10s", "5m").
    """
    store = HistoryStore()
    codes = store.load_last_batch()
    if not codes:
        print("No previous query found.")
        return

    if watch:
        _watch_loop(",".join(codes), _parse_duration(watch))
        return

    print(f"Re-querying: {', '.join(codes)}")
    run_query(",".join(codes), save_history=False)


def run_watchlist(action: str | None, codes_str: str | None, clear: bool, list_only: bool) -> None:
    """Manage watchlist: add, remove, clear, list, or interactive picker."""
    store = HistoryStore()

    if clear:
        store.watchlist_clear()
        print("Watchlist cleared.")
        return

    if action == "add" and codes_str:
        codes = [c.strip() for c in codes_str.split(",") if c.strip()]
        added = []
        for c in codes:
            name = store.lookup_name(c) or ""
            store.watchlist_add(c, name)
            added.append(c)
        print(f"Added to watchlist: {', '.join(added)}")
        return

    if action == "rm" and codes_str:
        codes = [c.strip() for c in codes_str.split(",") if c.strip()]
        removed = store.watchlist_remove(codes)
        if removed:
            print(f"Removed from watchlist: {', '.join(removed)}")
        else:
            print("No matching stocks in watchlist.")
        return

    entries = store.watchlist_load()
    if not entries:
        print("Watchlist is empty. Add stocks with: stock_query watchlist add <code>")
        return

    if list_only:
        for i, (code, name) in enumerate(entries, 1):
            label = f"{name}" if name else "-"
            print(f"  {i:>3}. {code:<12} {label}")
        return

    # Interactive picker
    selected = pick(entries)
    if selected:
        run_query(",".join(selected), save_history=False)
    else:
        print("Cancelled.")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "query":
        codes_str = " ".join(args.codes)
        if args.watch:
            _watch_loop(codes_str, _parse_duration(args.watch))
        else:
            run_query(codes_str)
    elif args.command == "last":
        run_last(watch=args.watch)
    elif args.command == "complete":
        run_complete(args.prefix)
    elif args.command == "shell-completions":
        print(_get_bash_completion())
    elif args.command == "history":
        run_history(args.pick, args.remove, args.clear, args.list)
    elif args.command == "watchlist":
        run_watchlist(args.action, args.codes, args.clear, args.list)
    elif args.command == "repl":
        from stock_query.repl import run_repl
        run_repl()
    elif args.command == "refresh-namelist":
        from stock_query.namelist import NameList
        from stock_query.store import HistoryStore
        from datetime import datetime
        nl = NameList(HistoryStore().db_path)
        before = nl.count()
        count = nl.refresh(force=args.force)
        if count == before and count > 0:
            info = nl.status()
            ts = info["last_refresh"]
            ago = ""
            if ts:
                secs = int(datetime.now().timestamp() - ts)
                if secs < 120:
                    ago = f" ({secs}s ago)"
                elif secs < 7200:
                    ago = f" ({secs // 60}m ago)"
                else:
                    ago = f" ({secs // 3600}h ago)"
            print(f"Name list cached: {count} A-share stocks{ago}. Use --force to re-download.")
    else:
        parser.print_help()
        sys.exit(1)
