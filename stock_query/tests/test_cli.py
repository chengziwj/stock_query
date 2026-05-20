import pytest
from unittest.mock import patch
from stock_query.cli import build_parser, run_query

SAMPLE_RAW = (
    'v_sz000001="1~平安银行~000001~10.50~10.40~10.60~100000~'
    '5000~1000~100~200~300~400~500~100~200~300~400~500~'
    '200~300~400~500~100~200~300~400~500~2025-05-20~14:30:00~'
    '0.10~0.96~10.60~10.30~120000~600000~2.50~8.50~'
    '0.00~11.44~9.36~3.00~50000000000~60000000000~1.20"\n'
)


def test_build_parser():
    parser = build_parser()
    args = parser.parse_args(["query", "000001,600000"])
    assert args.codes == "000001,600000"


def test_run_query_single(capsys):
    with patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.return_value = SAMPLE_RAW
        run_query("000001")
    captured = capsys.readouterr()
    assert "平安银行" in captured.out


def test_run_query_batch(capsys):
    with patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.return_value = SAMPLE_RAW
        run_query("000001,600000")
    captured = capsys.readouterr()
    assert "平安银行" in captured.out


def test_run_query_network_error(capsys):
    import requests
    with patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.side_effect = requests.ConnectionError("no net")
        run_query("000001")
    captured = capsys.readouterr()
    assert "error" in captured.out.lower() or "Error" in captured.out
