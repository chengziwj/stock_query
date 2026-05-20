"""Integration test with real Tencent API."""
import pytest
from stock_query.fetcher import fetch_quotes, infer_prefix
from stock_query.parser import parse_quotes
from stock_query.formatter import format_quotes


@pytest.mark.integration
def test_end_to_end_single():
    codes = [infer_prefix("000001")]
    raw = fetch_quotes(codes)
    assert raw, "should get non-empty response"
    stocks = parse_quotes(raw)
    assert len(stocks) == 1
    assert stocks[0]["name"], "should have a name"
    assert stocks[0]["code"] == "000001"


@pytest.mark.integration
def test_end_to_end_batch():
    codes = [infer_prefix("000001"), infer_prefix("600000")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    assert len(stocks) == 2


@pytest.mark.integration
def test_end_to_end_hk():
    codes = [infer_prefix("00700")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    assert len(stocks) == 1


@pytest.mark.integration
def test_end_to_end_us():
    codes = [infer_prefix("AAPL")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    assert len(stocks) == 1


@pytest.mark.integration
def test_format_output_no_crash():
    codes = [infer_prefix("000001")]
    raw = fetch_quotes(codes)
    stocks = parse_quotes(raw)
    # Should not raise
    format_quotes(stocks)
