import os
import tempfile
from contextlib import contextmanager

import pytest

from stock_query.repl import _Completer
from stock_query.store import HistoryStore


@contextmanager
def _temp_db(name: str = "test.db"):
    """Context manager yielding a path to a temp SQLite file, auto-cleaned."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, name)


class TestHistoryStore:
    def test_add_and_load(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            entries = store.load()
            assert len(entries) == 2
            assert entries[0] == ("600000", "浦发银行")  # most recent first
            assert entries[1] == ("000001", "平安银行")

    def test_add_deduplicates(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            store.add("000001", "平安银行")  # duplicate — upsert
            entries = store.load()
            assert len(entries) == 1

    def test_add_prunes_oldest(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path, max_entries=3)
            store.add("000001", "a")
            store.add("000002", "b")
            store.add("000003", "c")
            store.add("000004", "d")  # pushes out oldest (000001)
            entries = store.load()
            assert len(entries) == 3
            codes = [c for c, _ in entries]
            assert "000004" in codes
            assert "000001" not in codes

    def test_clear(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            store.clear()
            assert store.entry_count() == 0

    def test_load_empty(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            assert store.load() == []

    def test_remove_by_index(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            store.add("000002", "万科A")
            # Most recent first: 000002, 600000, 000001
            removed = store.remove_by_index([1, 3])
            assert len(removed) == 2
            assert removed[0][0] == "000002"  # index 1 = most recent
            assert removed[1][0] == "000001"  # index 3 = oldest
            entries = store.load()
            assert len(entries) == 1
            assert entries[0][0] == "600000"

    def test_get_by_index(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            store.add("000002", "万科A")
            codes = store.get_by_index([1, 3])
            assert codes == ["000002", "000001"]

    def test_get_by_index_out_of_range(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            codes = store.get_by_index([1, 5, 0])
            assert codes == ["000001"]

    def test_save_and_load_last_batch(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.save_last_batch(["000001", "600000", "AAPL"])
            codes = store.load_last_batch()
            assert codes == ["000001", "600000", "AAPL"]
            # Overwrite
            store.save_last_batch(["00700"])
            codes = store.load_last_batch()
            assert codes == ["00700"]

    def test_load_last_batch_empty(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            assert store.load_last_batch() == []

    def test_watchlist_add_and_load(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.watchlist_add("000001", "平安银行")
            store.watchlist_add("600000", "浦发银行")
            entries = store.watchlist_load()
            assert len(entries) == 2
            assert entries[0] == ("000001", "平安银行")
            assert entries[1] == ("600000", "浦发银行")

    def test_watchlist_remove(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.watchlist_add("000001", "平安银行")
            store.watchlist_add("600000", "浦发银行")
            removed = store.watchlist_remove(["000001"])
            assert removed == ["000001"]
            entries = store.watchlist_load()
            assert len(entries) == 1
            assert entries[0][0] == "600000"

    def test_watchlist_clear(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.watchlist_add("000001", "平安银行")
            store.watchlist_clear()
            assert store.watchlist_load() == []

    def test_lookup_name(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            assert store.lookup_name("000001") == "平安银行"
            assert store.lookup_name("nonexistent") is None


class TestCompleter:
    def test_complete_by_code(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            c = _Completer(store)
            assert c("000", 0) == "000001"
            assert c("000", 1) is None

    def test_complete_by_name(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            c = _Completer(store)
            assert c("平安", 0) == "000001"

    def test_complete_no_match(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            c = _Completer(store)
            assert c("xyz", 0) is None

    def test_complete_multiple_state(self):
        with _temp_db() as path:
            store = HistoryStore(db_path=path)
            store.add("000001", "a")
            store.add("000002", "b")
            store.add("000003", "c")
            c = _Completer(store)
            assert c("000", 0) == "000003"
            assert c("000", 1) == "000002"
            assert c("000", 2) == "000001"
            assert c("000", 3) is None


def test_repl_cli_subcommand():
    from stock_query.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["repl"])
    assert args.command == "repl"
