"""Interactive REPL with history-based Tab completion."""
from __future__ import annotations

import readline

from stock_query.query import execute_query
from stock_query.store import HistoryStore


class _Completer:
    """readline completer that matches codes/names from history.

    Caches entries for the duration of a single completion session
    (readline calls __call__ once per match, so caching avoids N SQLite reads).
    """

    def __init__(self, store: HistoryStore):
        self.store = store
        self._cached_text: str | None = None
        self._cached_matches: list[tuple[str, str]] = []

    def __call__(self, text: str, state: int) -> str | None:
        # Cache matches per completion session; invalidate on new text
        if state == 0 or self._cached_text != text:
            self._cached_text = text
            entries = self.store.load()
            text_lower = text.lower()
            self._cached_matches = [
                (c, n)
                for c, n in entries
                if c.startswith(text) or text_lower in n.lower()
            ]

        if state < len(self._cached_matches):
            code, _name = self._cached_matches[state]
            return code
        return None


def _cmd_history(store: HistoryStore) -> None:
    """Print query history."""
    entries = store.load()
    if not entries:
        print("No query history yet.")
    else:
        for code, name in entries:
            print(f"  {code}  {name}")


def _cmd_clear(store: HistoryStore) -> None:
    """Clear query history."""
    store.clear()
    print("History cleared.")


def _cmd_help(_store: HistoryStore | None = None) -> None:
    """Print REPL help."""
    print("Commands:")
    print("  <code>       Query stock(s), comma-separated (e.g. 000001,600000)")
    print("  history      Show query history")
    print("  clear        Clear query history")
    print("  help         Show this help")
    print("  quit         Exit REPL")
    print("  Tab          Auto-complete from history")


_REPL_COMMANDS: dict[str, callable] = {
    "history": _cmd_history,
    "clear": _cmd_clear,
    "help": _cmd_help,
}


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

        command = _REPL_COMMANDS.get(line.lower())
        if command is not None:
            command(store)
            continue

        # Query stocks — execute_query handles everything
        execute_query(line, store=store)
