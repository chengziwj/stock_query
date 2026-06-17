"""A-share stock name list: download from Sina Finance and cache locally."""
from __future__ import annotations

import sqlite3
import time
from contextlib import contextmanager

import requests

# Sina Finance API — A-share list (paginated, 100 per page)
_LIST_URL_SH = (
    "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "Market_Center.getHQNodeData"
    "?page={page}&num=100&sort=symbol&asc=1&node=sh_a"
)
_LIST_URL_SZ = (
    "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "Market_Center.getHQNodeData"
    "?page={page}&num=100&sort=symbol&asc=1&node=sz_a"
)
_TIMEOUT = 15
# Minimum interval between downloads (seconds)
_REFRESH_COOLDOWN = 300  # 5 minutes


class NameList:
    """Downloadable, cached A-share name→code lookup."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_table(self) -> None:
        with self._conn() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS namelist (
                code TEXT PRIMARY KEY,
                name TEXT NOT NULL
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS namelist_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )""")

    def _get_meta(self, key: str) -> str | None:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM namelist_meta WHERE key = ?", (key,)
            ).fetchone()
        return row[0] if row else None

    def _set_meta(self, key: str, value: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO namelist_meta (key, value) VALUES (?, ?)",
                (key, value),
            )

    def count(self) -> int:
        """Return number of cached stocks."""
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) FROM namelist").fetchone()
        return row[0] if row else 0

    def status(self) -> dict:
        """Return cache status: count, last_refresh timestamp."""
        self._ensure_table()
        last_ts = self._get_meta("last_refresh")
        return {
            "count": self.count(),
            "last_refresh": float(last_ts) if last_ts else None,
        }

    def refresh(self, force: bool = False) -> int:
        """Download the full A-share stock list from Sina Finance.

        Args:
            force: If True, bypass the rate-limit cooldown.

        Returns the number of stocks loaded.
        """
        self._ensure_table()

        # Rate-limit: don't re-download within cooldown
        if not force:
            last_ts = self._get_meta("last_refresh")
            if last_ts:
                elapsed = time.time() - float(last_ts)
                if elapsed < _REFRESH_COOLDOWN:
                    remaining = int(_REFRESH_COOLDOWN - elapsed)
                    print(f"Stock list was refreshed {int(elapsed)}s ago. "
                          f"Please wait {remaining}s or use '--force' to skip cooldown. "
                          f"Currently cached: {self.count()} stocks.")
                    return self.count()

        print("Downloading A-share stock list from Sina Finance...")
        all_stocks: list[tuple[str, str]] = []

        for market, url_template in [("Shanghai", _LIST_URL_SH), ("Shenzhen", _LIST_URL_SZ)]:
            page = 1
            while True:
                url = url_template.format(page=page)
                try:
                    resp = requests.get(url, timeout=_TIMEOUT)
                    resp.raise_for_status()
                    try:
                        batch = resp.json()
                    except ValueError:
                        print(f"  Warning: invalid response for {market} page {page}, skipping.")
                        break
                except requests.RequestException as e:
                    print(f"Error: failed to download {market} page {page} — {e}")
                    print("Tip: you can still query by stock code (e.g. 000001 600000).")
                    print("     Try 'stock_query refresh-namelist' later to retry.")
                    return self.count()

                if not isinstance(batch, list) or not batch:
                    break

                for item in batch:
                    code = item.get("code", "").strip()
                    name = item.get("name", "").strip()
                    if code and name:
                        # Sina API returns names with spaces between chars (e.g. "五 粮 液")
                        name = name.replace(" ", "")
                        all_stocks.append((code, name))

                if len(batch) < 100:
                    break  # last page
                page += 1
                time.sleep(0.3)  # be polite to the API

        if not all_stocks:
            print("Error: no stock data received from Sina API.")
            return self.count()

        # Atomic replace
        with self._conn() as conn:
            conn.execute("DELETE FROM namelist")
            conn.executemany(
                "INSERT INTO namelist (code, name) VALUES (?, ?)",
                all_stocks,
            )

        self._set_meta("last_refresh", str(time.time()))
        print(f"Loaded {len(all_stocks)} A-share stocks into local cache.")
        return len(all_stocks)

    def search_by_name(self, name: str, limit: int = 10) -> list[tuple[str, str]]:
        """Fuzzy-search stocks by name. Returns list of (code, name)."""
        self._ensure_table()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT code, name FROM namelist WHERE name LIKE ? "
                "ORDER BY LENGTH(name) LIMIT ?",
                (f"%{name}%", limit),
            ).fetchall()
        return [(r[0], r[1]) for r in rows]

    def resolve_name(self, name: str) -> str | None:
        """Resolve a single stock name to its code. Returns None if not found.

        Matching order: exact → prefix → contains (shortest match).

        Auto-refreshes the stock list on first use if empty.
        """
        name = name.replace(" ", "")  # normalize (Sina names have no spaces)
        self._ensure_table()
        if self.count() == 0:
            print("Stock name list is empty, downloading...")
            self.refresh()
            if self.count() == 0:
                print("Tip: you can still query by stock code directly (e.g. 000001 600000).")
                return None
        with self._conn() as conn:
            # 1) Exact match
            row = conn.execute(
                "SELECT code FROM namelist WHERE name = ?", (name,)
            ).fetchone()
            if row:
                return row[0]
            # 2) Prefix match — prefer lower code (more established stocks)
            row = conn.execute(
                "SELECT code FROM namelist WHERE name LIKE ? "
                "ORDER BY code LIMIT 1",
                (f"{name}%",),
            ).fetchone()
            if row:
                return row[0]
            # 3) Contains match — prefer shortest name, then lower code
            row = conn.execute(
                "SELECT code FROM namelist WHERE name LIKE ? "
                "ORDER BY LENGTH(name), code LIMIT 1",
                (f"%{name}%",),
            ).fetchone()
            if row:
                return row[0]
        return None

    def get_code(self, name: str) -> str | None:
        """Alias for resolve_name."""
        return self.resolve_name(name)
