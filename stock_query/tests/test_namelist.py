import os
import tempfile
from contextlib import contextmanager

import pytest

from stock_query.namelist import NameList
from stock_query.query import _is_name_like, _resolve_codes


@contextmanager
def _temp_db(name: str = "test.db"):
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, name)


class TestIsNameLike:
    def test_chinese_is_name(self):
        assert _is_name_like("平安银行") is True

    def test_short_alpha_is_code(self):
        assert _is_name_like("AAPL") is False
        assert _is_name_like("TSLA") is False

    def test_long_alpha_is_name(self):
        assert _is_name_like("AppleInc") is True

    def test_digits_is_code(self):
        assert _is_name_like("000001") is False
        assert _is_name_like("600000") is False


class TestNameList:
    def test_refresh_and_resolve(self):
        with _temp_db() as path:
            nl = NameList(path)
            # Mock the HTTP call — just test the DB operations
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("000001", "平安银行"),
                )
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("600519", "贵州茅台"),
                )
            assert nl.count() == 2
            assert nl.resolve_name("平安银行") == "000001"
            assert nl.resolve_name("贵州茅台") == "600519"

    def test_resolve_prefix_match(self):
        with _temp_db() as path:
            nl = NameList(path)
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("000001", "平安银行"),
                )
            # Prefix match
            assert nl.resolve_name("平安") == "000001"

    def test_resolve_contains_match(self):
        with _temp_db() as path:
            nl = NameList(path)
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("600519", "贵州茅台"),
                )
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("000858", "五粮液"),
                )
            # Substring: "茅台" → "贵州茅台"
            assert nl.resolve_name("茅台") == "600519"
            # "粮液" → "五粮液"
            assert nl.resolve_name("粮液") == "000858"

    def test_resolve_contains_prefers_shortest(self):
        with _temp_db() as path:
            nl = NameList(path)
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("600519", "贵州茅台"),
                )
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("999999", "贵州茅台酒股份"),
                )
            # Both contain "茅台"; prefix doesn't match, falls to contains
            # Contains picks shortest name → 贵州茅台
            assert nl.resolve_name("茅台") == "600519"

    def test_resolve_prefix_prefers_lower_code(self):
        with _temp_db() as path:
            nl = NameList(path)
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("301260", "格力博"),
                )
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("000651", "格力电器"),
                )
            # Both prefix-match "格力"; lower code wins
            assert nl.resolve_name("格力") == "000651"

    def test_resolve_not_found(self):
        with _temp_db() as path:
            nl = NameList(path)
            nl._ensure_table()
            assert nl.resolve_name("不存在的股票") is None

    def test_search_by_name(self):
        with _temp_db() as path:
            nl = NameList(path)
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("000001", "平安银行"),
                )
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("601318", "中国平安"),
                )
            results = nl.search_by_name("平安")
            assert len(results) == 2
            codes = {c for c, _ in results}
            assert codes == {"000001", "601318"}


class TestResolveCodes:
    def test_resolve_name(self):
        with _temp_db() as path:
            # Pre-populate namelist
            nl = NameList(path)
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("000001", "平安银行"),
                )
            result = _resolve_codes(["平安银行"], path)
            assert result == ["sz000001"]

    def test_resolve_code_passthrough(self):
        with _temp_db() as path:
            result = _resolve_codes(["000001", "AAPL"], path)
            assert result == ["sz000001", "usAAPL"]

    def test_resolve_mixed(self):
        with _temp_db() as path:
            nl = NameList(path)
            nl._ensure_table()
            with nl._conn() as conn:
                conn.execute(
                    "INSERT INTO namelist (code, name) VALUES (?, ?)",
                    ("600519", "贵州茅台"),
                )
            result = _resolve_codes(["贵州茅台", "000001", "AAPL"], path)
            assert result == ["sh600519", "sz000001", "usAAPL"]
