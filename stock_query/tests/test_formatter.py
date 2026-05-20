import pytest
from stock_query.formatter import format_quotes, format_value

SINGLE_STOCK = [{
    "code": "000001", "name": "平安银行", "price": "10.50",
    "change": "0.10", "change_pct": "0.96",
    "open": "10.40", "prev_close": "10.40",
    "high": "10.60", "low": "10.30",
    "volume_total": "120000", "amount": "600000",
    "turnover": "2.50", "pe_ratio": "8.50",
    "amplitude": "3.00", "market_cap": "50000000000",
    "_raw": [],
}]

BATCH_STOCKS = [
    SINGLE_STOCK[0],
    {
        "code": "600000", "name": "浦发银行", "price": "8.90",
        "change": "-0.05", "change_pct": "-0.56",
        "open": "8.95", "prev_close": "8.95",
        "high": "9.00", "low": "8.85",
        "volume_total": "80000", "amount": "400000",
        "turnover": "1.80", "pe_ratio": "6.20",
        "amplitude": "1.68", "market_cap": "30000000000",
        "_raw": [],
    },
]


def test_format_value_price():
    assert format_value("price", "10.50") == "10.50"


def test_format_value_change_pct():
    assert format_value("change_pct", "0.96") == "+0.96%"


def test_format_value_volume():
    assert format_value("volume_total", "123456") == "123,456"


def test_format_value_market_cap():
    assert format_value("market_cap", "50000000000") == "50,000,000,000"


def test_format_value_unknown():
    assert format_value("name", "Test") == "Test"


def test_format_quotes_single_does_not_raise():
    # Single stock: renders vertical card (no exception)
    format_quotes(SINGLE_STOCK)


def test_format_quotes_batch_does_not_raise():
    # Batch: renders table (no exception)
    format_quotes(BATCH_STOCKS)


def test_format_quotes_empty():
    # Should not crash on empty
    format_quotes([])
