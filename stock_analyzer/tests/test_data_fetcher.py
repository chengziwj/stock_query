"""测试数据获取模块"""

import pytest
import pandas as pd
import numpy as np

from data_fetcher import StockCodeParser, DataFetcher


class TestStockCodeParser:
    """测试股票代码解析器"""

    def test_parse_6digit_sz_code(self):
        """测试深交所6位代码"""
        assert StockCodeParser.parse('000001') == '000001.SZ'
        assert StockCodeParser.parse('002594') == '002594.SZ'
        assert StockCodeParser.parse('300750') == '300750.SZ'

    def test_parse_6digit_sh_code(self):
        """测试上交所6位代码"""
        assert StockCodeParser.parse('600000') == '600000.SS'
        assert StockCodeParser.parse('688981') == '688981.SS'
        assert StockCodeParser.parse('600519') == '600519.SS'

    def test_parse_full_code(self):
        """测试完整代码格式"""
        assert StockCodeParser.parse('000001.SZ') == '000001.SZ'
        assert StockCodeParser.parse('600000.SS') == '600000.SS'
        assert StockCodeParser.parse('000001.sz') == '000001.SZ'
        assert StockCodeParser.parse('600000.ss') == '600000.SS'

    def test_parse_chinese_name(self):
        """测试中文名称"""
        assert StockCodeParser.parse('平安银行') == '000001.SZ'
        assert StockCodeParser.parse('贵州茅台') == '600519.SS'
        assert StockCodeParser.parse('招商银行') == '600036.SS'

    def test_parse_invalid_code(self):
        """测试无效代码"""
        with pytest.raises(ValueError):
            StockCodeParser.parse('invalid')

        with pytest.raises(ValueError):
            StockCodeParser.parse('12345')  # 非6位

        with pytest.raises(ValueError):
            StockCodeParser.parse('未知股票名')

    def test_is_chinese(self):
        """测试中文检测"""
        assert StockCodeParser._is_chinese('平安银行') is True
        assert StockCodeParser._is_chinese('000001') is False
        assert StockCodeParser._is_chinese('abc中国def') is True

    def test_add_exchange_suffix(self):
        """测试交易所后缀添加"""
        assert StockCodeParser._add_exchange_suffix('000001') == '000001.SZ'
        assert StockCodeParser._add_exchange_suffix('600000') == '600000.SS'
        assert StockCodeParser._add_exchange_suffix('688981') == '688981.SS'


class TestDataFetcher:
    """测试数据获取类"""

    def test_init(self):
        """测试初始化"""
        fetcher = DataFetcher()
        assert fetcher.token is None
        assert fetcher._pro is None

    def test_init_with_token(self):
        """测试带token初始化"""
        fetcher = DataFetcher(token='test_token')
        assert fetcher.token == 'test_token'

    def test_process_data(self):
        """测试数据处理"""
        fetcher = DataFetcher()

        # 创建测试数据
        df = pd.DataFrame({
            'trade_date': ['20240101', '20240102', '20240103'] * 10,
            'open': [10.0] * 30,
            'high': [10.5] * 30,
            'low': [9.5] * 30,
            'close': [10.2] * 30,
            'vol': [1000000] * 30
        })

        processed = fetcher._process_data(df)

        assert 'trade_date' in processed.columns
        assert 'close' in processed.columns
        assert len(processed) == 30
        # 验证日期是升序排列
        assert processed['trade_date'].is_monotonic_increasing