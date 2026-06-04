import os
import tempfile
import pytest
from unittest.mock import patch

from stock_query.repl import HistoryStore, _Completer


class TestHistoryStore:
    def test_add_and_load(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            entries = store.load()
            assert len(entries) == 2
            assert entries[0] == ("600000", "浦发银行")  # most recent first
            assert entries[1] == ("000001", "平安银行")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_add_deduplicates(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            store.add("000001", "平安银行")  # duplicate
            entries = store.load()
            assert len(entries) == 1
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_add_prunes_oldest(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path, max_entries=3)
            store.add("000001", "a")
            store.add("000002", "b")
            store.add("000003", "c")
            store.add("000004", "d")  # pushes out 000001
            entries = store.load()
            assert len(entries) == 3
            codes = [c for c, _ in entries]
            assert "000004" in codes
            assert "000001" not in codes
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_clear(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            store.clear()
            assert store.entry_count() == 0
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_load_empty(self):
        path = os.path.join(tempfile.mkdtemp(), "nonexistent")
        store = HistoryStore(path=path)
        assert store.load() == []

    def test_remove_by_index(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            store.add("000002", "万科A")
            # Remove indices 1 and 3 (1-based: most recent = 1)
            removed = store.remove_by_index([1, 3])
            assert len(removed) == 2
            assert removed[0][0] == "000002"  # most recent
            assert removed[1][0] == "000001"  # oldest
            # Only 600000 remains
            entries = store.load()
            assert len(entries) == 1
            assert entries[0][0] == "600000"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_get_by_index(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            store.add("000002", "万科A")
            codes = store.get_by_index([1, 3])
            assert codes == ["000002", "000001"]
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_get_by_index_out_of_range(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            codes = store.get_by_index([1, 5, 0])
            assert codes == ["000001"]  # only valid index
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_load_malformed_line(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            with open(path, "w") as f:
                f.write("000001 平安银行\n")
                f.write("\n")  # empty line
                f.write("code_only\n")
            store = HistoryStore(path=path)
            entries = store.load()
            assert len(entries) == 2
            assert entries[0] == ("000001", "平安银行")
            assert entries[1] == ("code_only", "")
        finally:
            if os.path.exists(path):
                os.remove(path)


class TestCompleter:
    def test_complete_by_code(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            c = _Completer(store)
            assert c("000", 0) == "000001"
            assert c("000", 1) is None  # only one match
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_complete_by_name(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "平安银行")
            store.add("600000", "浦发银行")
            c = _Completer(store)
            assert c("平安", 0) == "000001"
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_complete_no_match(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            c = _Completer(store)
            assert c("xyz", 0) is None
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_complete_multiple_state(self):
        path = os.path.join(tempfile.mkdtemp(), "test_history")
        try:
            store = HistoryStore(path=path)
            store.add("000001", "a")
            store.add("000002", "b")
            store.add("000003", "c")
            c = _Completer(store)
            assert c("000", 0) == "000003"  # most recent first
            assert c("000", 1) == "000002"
            assert c("000", 2) == "000001"
            assert c("000", 3) is None
        finally:
            if os.path.exists(path):
                os.remove(path)


def test_repl_cli_subcommand():
    # Verify the parser accepts "repl" as a subcommand
    from stock_query.cli import build_parser
    parser = build_parser()
    args = parser.parse_args(["repl"])
    assert args.command == "repl"
