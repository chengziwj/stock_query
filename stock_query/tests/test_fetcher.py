import pytest
from unittest.mock import patch, Mock
import requests
from stock_query.fetcher import infer_prefix, fetch_quotes


SAMPLE_RESPONSE = (
    'v_sz000001="1~平安银行~000001~10.50~0.10~0.96~10.40~10.60~10.45~10.30~100000~"\n'
    'v_sh600000="1~浦发银行~600000~8.90~-0.05~-0.56~8.95~8.96~9.00~8.85~50000~"\n'
)


@pytest.mark.parametrize("code,expected", [
    ("000001", "sz000001"),
    ("002001", "sz002001"),
    ("300001", "sz300001"),
    ("600000", "sh600000"),
    ("601000", "sh601000"),
    ("603000", "sh603000"),
    ("688000", "sh688000"),
    ("00700", "hk00700"),
    ("AAPL", "usAAPL"),
    ("TSLA", "usTSLA"),
])
def test_infer_prefix(code, expected):
    assert infer_prefix(code) == expected


def test_infer_prefix_already_prefixed():
    assert infer_prefix("sz000001") == "sz000001"
    assert infer_prefix("sh600000") == "sh600000"
    assert infer_prefix("hk00700") == "hk00700"
    assert infer_prefix("usAAPL") == "usAAPL"


def test_infer_prefix_empty():
    with pytest.raises(ValueError, match="empty"):
        infer_prefix("")


def test_infer_prefix_unknown():
    with pytest.raises(ValueError, match="Cannot infer"):
        infer_prefix("12345")


def test_fetch_quotes_single():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            text=SAMPLE_RESPONSE,
        )
        result = fetch_quotes(["sz000001"])
        assert "v_sz000001" in result
        mock_get.assert_called_once()
        url = mock_get.call_args[0][0]
        assert "sz000001" in url
        assert url.startswith("http://qt.gtimg.cn/q=")


def test_fetch_quotes_batch():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, text=SAMPLE_RESPONSE)
        result = fetch_quotes(["sz000001", "sh600000"])
        url = mock_get.call_args[0][0]
        assert "sz000001" in url
        assert "sh600000" in url


def test_fetch_quotes_network_error():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.side_effect = requests.ConnectionError("no network")
        with pytest.raises(requests.ConnectionError):
            fetch_quotes(["sz000001"])


def test_fetch_quotes_http_error():
    with patch("stock_query.fetcher.requests.get") as mock_get:
        mock_get.return_value = Mock(status_code=500, text="error")
        result = fetch_quotes(["sz000001"])
        assert result == ""
