import pytest
from unittest.mock import patch, call
from stock_query.cli import build_parser, run_query, run_complete, run_history, run_last, run_watchlist, _parse_duration, _parse_index_list


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


def test_build_parser_complete():
    parser = build_parser()
    args = parser.parse_args(["complete", "000"])
    assert args.prefix == "000"


def test_build_parser_complete_no_args():
    parser = build_parser()
    args = parser.parse_args(["complete"])
    assert args.prefix == ""


def test_build_parser_shell_completions():
    parser = build_parser()
    args = parser.parse_args(["shell-completions"])
    assert args.command == "shell-completions"


def test_build_parser_history():
    parser = build_parser()
    args = parser.parse_args(["history"])
    assert args.command == "history"
    assert args.pick is None
    assert args.remove is None
    assert args.clear is False


def test_build_parser_history_pick():
    parser = build_parser()
    args = parser.parse_args(["history", "--pick", "1,3,5"])
    assert args.pick == "1,3,5"


def test_build_parser_history_rm():
    parser = build_parser()
    args = parser.parse_args(["history", "--rm", "2,4"])
    assert args.remove == "2,4"


def test_build_parser_history_clear():
    parser = build_parser()
    args = parser.parse_args(["history", "--clear"])
    assert args.clear is True


def test_build_parser_history_list():
    parser = build_parser()
    args = parser.parse_args(["history", "--list"])
    assert args.list is True


def test_build_parser_last():
    parser = build_parser()
    args = parser.parse_args(["last"])
    assert args.command == "last"


def test_parse_index_list():
    assert _parse_index_list("1,3,5") == [1, 3, 5]
    assert _parse_index_list(" 2 , 4 ") == [2, 4]
    assert _parse_index_list("1") == [1]


def test_parse_index_list_invalid():
    with pytest.raises(ValueError):
        _parse_index_list("1,abc,3")


def test_run_query_single(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls, \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.return_value = SAMPLE_RAW
        run_query("000001")
    captured = capsys.readouterr()
    assert "平安银行" in captured.out
    mock_store_cls.return_value.save_last_batch.assert_called_once_with(["000001"])
    mock_store_cls.return_value.add.assert_called()


def test_run_query_batch(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls, \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.return_value = SAMPLE_RAW
        run_query("000001,600000")
    captured = capsys.readouterr()
    assert "平安银行" in captured.out
    mock_store_cls.return_value.save_last_batch.assert_called_once_with(["000001", "600000"])
    mock_store_cls.return_value.add.assert_called()


def test_run_query_network_error(capsys):
    import requests
    with patch("stock_query.cli.HistoryStore"), \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_fetch.side_effect = requests.ConnectionError("no net")
        run_query("000001")
    captured = capsys.readouterr()
    assert "error" in captured.out.lower() or "Error" in captured.out


def test_run_complete_matches_code(capsys):
    fake_entries = [("000001", "平安银行"), ("600000", "浦发银行"), ("AAPL", "Apple")]
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.load.return_value = fake_entries
        run_complete("000")
    captured = capsys.readouterr()
    assert "000001" in captured.out


def test_run_complete_matches_name(capsys):
    fake_entries = [("000001", "平安银行"), ("AAPL", "Apple")]
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.load.return_value = fake_entries
        run_complete("平安")
    captured = capsys.readouterr()
    assert "000001" in captured.out


def test_run_complete_empty(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.load.return_value = []
        run_complete("xyz")
    captured = capsys.readouterr()
    assert captured.out.strip() == ""


def test_run_history_list(capsys):
    fake_entries = [("600000", "浦发银行"), ("000001", "平安银行")]
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.load.return_value = fake_entries
        run_history(pick_val=None, remove=None, clear=False, list_only=True)
    captured = capsys.readouterr()
    assert "1." in captured.out
    assert "2." in captured.out
    assert "浦发银行" in captured.out
    assert "平安银行" in captured.out


def test_run_history_list_empty(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.load.return_value = []
        run_history(pick_val=None, remove=None, clear=False, list_only=True)
    captured = capsys.readouterr()
    assert "No query history" in captured.out


def test_run_history_clear(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        run_history(pick_val=None, remove=None, clear=True, list_only=False)
    captured = capsys.readouterr()
    assert "cleared" in captured.out.lower()
    mock_store_cls.return_value.clear.assert_called_once()


def test_run_history_remove(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.remove_by_index.return_value = [
            ("000001", "平安银行"),
        ]
        run_history(pick_val=None, remove="1", clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "Removed:" in captured.out
    assert "平安银行" in captured.out
    mock_store_cls.return_value.remove_by_index.assert_called_once_with([1])


def test_run_history_remove_none_found(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.remove_by_index.return_value = []
        run_history(pick_val=None, remove="1", clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "No matching" in captured.out


def test_run_history_pick(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls, \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_store_cls.return_value.get_by_index.return_value = ["000001", "600000"]
        mock_fetch.return_value = SAMPLE_RAW
        run_history(pick_val="1,2", remove=None, clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "平安银行" in captured.out
    mock_store_cls.return_value.get_by_index.assert_called_once_with([1, 2])
    mock_store_cls.return_value.add.assert_not_called()


def test_run_history_interactive(capsys):
    fake_entries = [("600000", "浦发银行"), ("000001", "平安银行")]
    with patch("stock_query.cli.HistoryStore") as mock_store_cls, \
         patch("stock_query.cli.pick") as mock_pick, \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_store_cls.return_value.load.return_value = fake_entries
        mock_pick.return_value = ["000001"]
        mock_fetch.return_value = SAMPLE_RAW
        run_history(pick_val=None, remove=None, clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "平安银行" in captured.out
    mock_pick.assert_called_once_with(fake_entries)
    mock_store_cls.return_value.add.assert_not_called()


def test_run_history_interactive_cancel(capsys):
    fake_entries = [("600000", "浦发银行")]
    with patch("stock_query.cli.HistoryStore") as mock_store_cls, \
         patch("stock_query.cli.pick") as mock_pick, \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_store_cls.return_value.load.return_value = fake_entries
        mock_pick.return_value = []
        run_history(pick_val=None, remove=None, clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "Cancelled" in captured.out
    mock_fetch.assert_not_called()


def test_run_last(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls, \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_store_cls.return_value.load_last_batch.return_value = ["000001", "600000"]
        mock_fetch.return_value = SAMPLE_RAW
        run_last()
    captured = capsys.readouterr()
    assert "Re-querying" in captured.out
    assert "平安银行" in captured.out


def test_run_last_empty(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.load_last_batch.return_value = []
        run_last()
    captured = capsys.readouterr()
    assert "No previous query" in captured.out


def test_build_parser_watchlist():
    parser = build_parser()
    args = parser.parse_args(["watchlist"])
    assert args.command == "watchlist"


def test_build_parser_watchlist_add():
    parser = build_parser()
    args = parser.parse_args(["watchlist", "add", "000001,600000"])
    assert args.action == "add"
    assert args.codes == "000001,600000"


def test_build_parser_watchlist_clear():
    parser = build_parser()
    args = parser.parse_args(["watchlist", "--clear"])
    assert args.clear is True


def test_run_watchlist_add(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.lookup_name.return_value = "平安银行"
        run_watchlist(action="add", codes_str="000001,600000", clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "Added to watchlist" in captured.out
    assert "000001" in captured.out
    assert mock_store_cls.return_value.watchlist_add.call_count == 2


def test_run_watchlist_rm(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.watchlist_remove.return_value = ["000001"]
        run_watchlist(action="rm", codes_str="000001", clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "Removed from watchlist" in captured.out


def test_run_watchlist_rm_not_found(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.watchlist_remove.return_value = []
        run_watchlist(action="rm", codes_str="000001", clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "No matching" in captured.out


def test_run_watchlist_clear(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        run_watchlist(action=None, codes_str=None, clear=True, list_only=False)
    captured = capsys.readouterr()
    assert "cleared" in captured.out.lower()
    mock_store_cls.return_value.watchlist_clear.assert_called_once()


def test_run_watchlist_list(capsys):
    fake_entries = [("000001", "平安银行"), ("600000", "浦发银行")]
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.watchlist_load.return_value = fake_entries
        run_watchlist(action=None, codes_str=None, clear=False, list_only=True)
    captured = capsys.readouterr()
    assert "平安银行" in captured.out
    assert "浦发银行" in captured.out


def test_run_watchlist_empty(capsys):
    with patch("stock_query.cli.HistoryStore") as mock_store_cls:
        mock_store_cls.return_value.watchlist_load.return_value = []
        run_watchlist(action=None, codes_str=None, clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "empty" in captured.out.lower()


def test_run_watchlist_interactive(capsys):
    fake_entries = [("000001", "平安银行")]
    with patch("stock_query.cli.HistoryStore") as mock_store_cls, \
         patch("stock_query.cli.pick") as mock_pick, \
         patch("stock_query.cli.fetch_quotes") as mock_fetch:
        mock_store_cls.return_value.watchlist_load.return_value = fake_entries
        mock_pick.return_value = ["000001"]
        mock_fetch.return_value = SAMPLE_RAW
        run_watchlist(action=None, codes_str=None, clear=False, list_only=False)
    captured = capsys.readouterr()
    assert "平安银行" in captured.out


def test_parse_duration_seconds():
    assert _parse_duration("10s") == 10
    assert _parse_duration("5") == 5
    assert _parse_duration(" 30 ") == 30


def test_parse_duration_minutes():
    assert _parse_duration("5m") == 300
    assert _parse_duration("1m") == 60


def test_parse_duration_hours():
    assert _parse_duration("1h") == 3600
    assert _parse_duration("2h") == 7200


def test_parse_duration_invalid():
    with pytest.raises(ValueError):
        _parse_duration("abc")
    with pytest.raises(ValueError):
        _parse_duration("")


def test_build_parser_query_watch():
    parser = build_parser()
    args = parser.parse_args(["query", "000001", "--watch", "10s"])
    assert args.watch == "10s"


def test_build_parser_last_watch():
    parser = build_parser()
    args = parser.parse_args(["last", "--watch", "5m"])
    assert args.watch == "5m"
