import pytest
from stock_query.parser import parse_quotes, get_market

A_SHARE_RESPONSE = (
    'v_sz000001="1~平安银行~000001~10.50~10.40~10.60~100000~5000~'
    '1000~100~200~300~400~500~100~200~300~400~500~200~300~400~500~'
    '100~200~300~400~500~2025-05-20~14:30:00~0.10~0.96~'
    '10.60~10.30~120000~600000~2.50~8.50~0.00~11.44~9.36~'
    '3.00~50000000000~60000000000~1.20"\n'
)

HK_RESPONSE = (
    'v_hk00700="1~腾讯控股~00700~380.00~375.00~382.00~1000000~'
    '500000000~1.20~385.00~380.00~2025/05/20~14:30:00~'
    '5.00~1.33~4.50"\n'
)

US_RESPONSE = (
    'v_usAAPL="Apple Inc~AAPL~190.50~1.50~0.79~189.00~191.00~'
    '190.00~188.50~50000000~2025/05/20~14:30:00"\n'
)


def test_parse_quotes_a_share():
    result = parse_quotes(A_SHARE_RESPONSE)
    assert len(result) == 1
    stock = result[0]
    assert stock["code"] == "000001"
    assert stock["name"] == "平安银行"
    assert stock["price"] == "10.50"


def test_parse_quotes_batch():
    response = A_SHARE_RESPONSE + HK_RESPONSE
    result = parse_quotes(response)
    assert len(result) == 2


def test_parse_quotes_empty():
    result = parse_quotes("")
    assert result == []


def test_parse_quotes_no_match():
    result = parse_quotes("garbage data\nno match here\n")
    assert result == []


def test_get_market():
    assert get_market("sz000001") == "sz"
    assert get_market("sh600000") == "sh"
    assert get_market("hk00700") == "hk"
    assert get_market("usAAPL") == "us"


def test_parse_quotes_hk():
    result = parse_quotes(HK_RESPONSE)
    assert len(result) == 1
    stock = result[0]
    assert stock["code"] == "00700"
    assert stock["name"] == "腾讯控股"
    assert stock["price"] == "380.00"
    assert stock["pe_ratio"] == "4.50"


def test_parse_quotes_us():
    result = parse_quotes(US_RESPONSE)
    assert len(result) == 1
    stock = result[0]
    assert stock["code"] == "AAPL"
    assert stock["name"] == "Apple Inc"
    assert stock["price"] == "190.50"
    assert stock["change"] == "1.50"
    assert stock["change_pct"] == "0.79"


def test_parse_preserves_all_fields():
    result = parse_quotes(A_SHARE_RESPONSE)
    stock = result[0]
    assert len(stock["_raw"]) == 45  # A-share has 45 fields in test data
    assert stock["_raw"][2] == "000001"
    assert stock["_raw"][1] == "平安银行"
