# stock_query — 股票实时行情 CLI

基于腾讯财经接口的 Python CLI 工具，支持 A 股（沪深）、港股、美股实时行情查询。

## Project

- **Stack:** Python ≥3.10, `requests` + `rich`, built with `hatchling`.
- **Entry points:** `stock_query.cli:main` (CLI via `stock-query` script), `stock_query/__main__.py` (`python -m stock_query`).
- **Package manager:** [uv](https://docs.astral.sh/uv/) (`uv sync` to install, `uv run` to execute).
- **Data:** SQLite db at `.data/stock_query.db` (gitignored) — tables `history`, `last_batch`, `watchlist`, `namelist`, `namelist_meta`.

## Commands

```bash
# Install
uv sync

# Run
uv run stock-query query 000001,600000,00700,AAPL
uv run stock-query history
uv run stock-query last
uv run stock-query repl

# Watch mode
uv run stock-query query 000001,600000 --watch 10s
uv run stock-query last --watch 5m

# Tests
uv run pytest stock_query/tests/ -v                         # all
uv run pytest stock_query/tests/ -v -m "not integration"    # skip network
```

## Architecture

| Module | Role |
|---|---|
| `cli.py` | argparse CLI — subcommands: `query`, `history`, `last`, `watchlist`, `repl`, `refresh-namelist`, `complete`, `shell-completions` |
| `fetcher.py` | HTTP client for `qt.gtimg.cn`; `infer_prefix()` maps code patterns → `sz`/`sh`/`hk`/`us` prefix |
| `parser.py` | Parses Tencent's `v_xxx="field~field~..."` response; per-market field-name mapping |
| `query.py` | Shared query pipeline (`execute_query`): resolve names/codes → fetch → parse → format → persist |
| `formatter.py` | Rich output: single-stock card mode, multi-stock table mode; red/green color for change |
| `store.py` | `HistoryStore` — SQLite persistence for history/last_batch/watchlist |
| `namelist.py` | `NameList` — downloads A-share name→code mapping from Sina, cached in same SQLite DB |
| `picker.py` | curses-based interactive multi-select picker |
| `repl.py` | Interactive REPL with tab-completion |

## Conventions

- **Imports:** `from __future__ import annotations` in every module.
- **Type hints:** Full type annotations on function signatures and instance variables; `list[dict]`/`str | None` style (not `Optional`).
- **Docstrings:** Google-style for public functions; brief one-liner module docstrings.
- **Error handling:** Network errors surfaced via exceptions in `fetcher.py`, caught and printed in `query.py`/CLI. Invalid codes produce warnings, not crashes.
- **Testing:** `pytest` with `unittest.mock.patch`; fixtures in `conftest.py`; integration tests gated behind `@pytest.mark.integration`.
- **Naming:** `snake_case` for functions/vars; `UPPER_CASE` for module-level constants; `_leading_underscore` for internal helpers.
- **Patterns:** Lazy singleton (`_get_console()`), `@contextmanager` for DB connections (commit on success, close always), atomic replace for cache updates.
- **No:** No classes-as-namespaces; no `@dataclass` usage; no logging framework (uses `print` for user-facing output).

## Notes

-
