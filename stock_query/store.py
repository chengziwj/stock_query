"""SQLite-backed persistence layer for stock query history, last batch, and watchlist."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager

_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DB_DIR = os.path.join(_PROJECT_DIR, ".data")
_DB_PATH = os.path.join(_DB_DIR, "stock_query.db")
_MAX_HISTORY = 100


class HistoryStore:
    """SQLite-backed query history, last-batch, and watchlist store."""

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

    # ── history ────────────────────────────────────────────────────

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

    # ── last_batch ─────────────────────────────────────────────────

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
