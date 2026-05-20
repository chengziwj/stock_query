"""Interactive REPL with history-based Tab completion."""
from __future__ import annotations

import os
import readline
import sys

from stock_query.fetcher import fetch_quotes, infer_prefix
from stock_query.parser import parse_quotes
from stock_query.formatter import format_quotes

_HISTORY_FILE = os.path.expanduser("~/.stock_query_history")
_MAX_HISTORY = 100


class HistoryStore:
    """Manage query history file: read, write, deduplicate, prune."""

    def __init__(self, path: str = _HISTORY_FILE, max_entries: int = _MAX_HISTORY):
        self.path = path
        self.max_entries = max_entries

    def _read(self) -> list[str]:
        if not os.path.exists(self.path):
            return []
        with open(self.path) as f:
            return [line.rstrip("\n") for line in f if line.strip()]

    def load(self) -> list[tuple[str, str]]:
        """Return list of (code, name) tuples."""
        entries = []
        for line in self._read():
            parts = line.split(None, 1)
            code = parts[0]
            name = parts[1] if len(parts) > 1 else ""
            entries.append((code, name))
        return entries

    def add(self, code: str, name: str) -> None:
        """Record a successful query. Deduplicate and prune."""
        entries = self._read()
        new_line = f"{code} {name}"
        # Remove existing entry for this code
        entries = [e for e in entries if not e.startswith(code + " ") and e != code]
        entries.insert(0, new_line)
        # Prune
        entries = entries[: self.max_entries]
        with open(self.path, "w") as f:
            for e in entries:
                f.write(e + "\n")

    def clear(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)

    def entry_count(self) -> int:
        return len(self._read())


class _Completer:
    """readline completer that matches codes/names from history."""

    def __init__(self, store: HistoryStore):
        self.store = store

    def __call__(self, text: str, state: int) -> str | None:
        entries = self.store.load()
        # Filter entries matching the input text (code or name prefix)
        text_lower = text.lower()
        matches = [
            (c, n)
            for c, n in entries
            if c.startswith(text) or text_lower in n.lower()
        ]
        if state < len(matches):
            code, name = matches[state]
            return code if name else code
        return None


def run_repl() -> None:
    """Start the interactive REPL loop."""
    store = HistoryStore()

    # Configure readline
    readline.parse_and_bind("tab: complete")
    readline.set_completer_delims(" \t\n;")
    readline.set_completer(_Completer(store))

    print("Stock Query REPL — type a code and press Enter, Tab to complete, 'quit' to exit")
    print()

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not line:
            continue

        if line.lower() in ("quit", "exit", "q"):
            break

        if line.lower() == "help":
            print("Commands:")
            print("  <code>       Query stock(s), comma-separated (e.g. 000001,600000)")
            print("  history      Show query history")
            print("  clear        Clear query history")
            print("  help         Show this help")
            print("  quit         Exit REPL")
            print("  Tab          Auto-complete from history")
            continue

        if line.lower() == "history":
            entries = store.load()
            if not entries:
                print("No query history yet.")
            else:
                for code, name in entries:
                    print(f"  {code}  {name}")
            continue

        if line.lower() == "clear":
            store.clear()
            print("History cleared.")
            continue

        # Parse codes
        codes = [c.strip() for c in line.split(",") if c.strip()]
        full_codes = []
        for c in codes:
            try:
                full_codes.append(infer_prefix(c))
            except ValueError as e:
                print(f"Warning: {e}")
                continue

        if not full_codes:
            continue

        try:
            raw = fetch_quotes(full_codes)
        except Exception as e:
            print(f"Error: network request failed — {e}")
            continue

        if not raw.strip():
            print("Error: received empty response from API.")
            continue

        stocks = parse_quotes(raw)
        if not stocks:
            print("Warning: no data returned.")
            continue

        format_quotes(stocks)

        # Record successful queries
        for code, stock in zip(codes, stocks):
            store.add(code, stock.get("name", ""))
