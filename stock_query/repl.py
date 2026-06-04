"""Interactive REPL with history-based Tab completion."""
from __future__ import annotations

import os
import readline
import sqlite3
from contextlib import contextmanager

from stock_query.fetcher import fetch_quotes, infer_prefix
from stock_query.formatter import format_quotes
from stock_query.parser import parse_quotes

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_DIR = os.path.join(_PROJECT_DIR, ".data")
_DB_PATH = os.path.join(_DB_DIR, "stock_query.db")
_MAX_HISTORY = 100


class HistoryStore:
    """SQLite-backed query history and last-batch store."""

    def __init__(self, db_path: str = _DB_PATH, max_entries: int = _MAX_HISTORY):
        self.db_path = db_path
        self.max_entries = max_entries
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS last_batch (
                code TEXT NOT NULL,
                seq INTEGER NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS watchlist (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )""")

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def load(self) -> list[tuple[str, str]]:
        """Return list of (code, name) tuples, most recent first."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT code, name FROM history ORDER BY id DESC LIMIT ?",
                (self.max_entries,),
            ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def add(self, code: str, name: str) -> None:
        """Record a query. Upsert and prune oldest if over max_entries."""
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO history (code, name) VALUES (?, ?)",
                (code, name),
            )
            count = conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]
            if count > self.max_entries:
                excess = count - self.max_entries
                conn.execute(
                    "DELETE FROM history WHERE id IN "
                    "(SELECT id FROM history ORDER BY id ASC LIMIT ?)",
                    (excess,),
                )

    def remove_by_index(self, indices: list[int]) -> list[tuple[str, str]]:
        """Remove entries by 1-based indices. Returns the removed entries."""
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT code, name FROM history ORDER BY id DESC"
            ).fetchall()
        removed = [(rows[i - 1][0], rows[i - 1][1]) for i in indices if 1 <= i <= len(rows)]
        with self._conn() as conn:
            for code, _ in removed:
                conn.execute("DELETE FROM history WHERE code = ?", (code,))
        return removed

    def get_by_index(self, indices: list[int]) -> list[str]:
        """Return stock codes at 1-based indices."""
        entries = self.load()
        return [entries[i - 1][0] for i in indices if 1 <= i <= len(entries)]

    def clear(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM history")

    def entry_count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM history").fetchone()[0]

    def save_last_batch(self, codes: list[str]) -> None:
        """Store the last queried batch of codes for quick re-query."""
        with self._conn() as conn:
            conn.execute("DELETE FROM last_batch")
            for i, code in enumerate(codes):
                conn.execute("INSERT INTO last_batch (code, seq) VALUES (?, ?)", (code, i))

    def load_last_batch(self) -> list[str]:
        """Return the last queried batch of codes in original order."""
        with self._conn() as conn:
            rows = conn.execute("SELECT code FROM last_batch ORDER BY seq").fetchall()
        return [r[0] for r in rows]

    # ── watchlist ──────────────────────────────────────────────────

    def watchlist_add(self, code: str, name: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO watchlist (code, name) VALUES (?, ?)",
                (code, name),
            )

    def watchlist_remove(self, codes: list[str]) -> list[str]:
        removed = []
        with self._conn() as conn:
            for c in codes:
                cur = conn.execute("DELETE FROM watchlist WHERE code = ?", (c,))
                if cur.rowcount:
                    removed.append(c)
        return removed

    def watchlist_load(self) -> list[tuple[str, str]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT code, name FROM watchlist ORDER BY code").fetchall()
        return [(r[0], r[1]) for r in rows]

    def watchlist_clear(self) -> None:
        with self._conn() as conn:
            conn.execute("DELETE FROM watchlist")

    def lookup_name(self, code: str) -> str | None:
        """Look up a stock name from history. Returns None if not found."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT name FROM history WHERE code = ?", (code,)
            ).fetchone()
        return row[0] if row else None


class _Completer:
    """readline completer that matches codes/names from history."""

    def __init__(self, store: HistoryStore):
        self.store = store

    def __call__(self, text: str, state: int) -> str | None:
        entries = self.store.load()
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
        store.save_last_batch(codes)
        for code, stock in zip(codes, stocks):
            store.add(code, stock.get("name", ""))
