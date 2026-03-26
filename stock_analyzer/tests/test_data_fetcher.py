"""测试数据获取模块"""

import pytest
import pandas as pd
import numpy as np

from data_fetcher import StockCodeParser, DataFetcher


class TestStockCodeParser:
    """测试股票代码解析器"""

    def test_parse_6digit_sz_code(self):
        """测试深交所6位代码"""
        assert StockCodeParser.parse('000001') == '000001'
        assert StockCodeParser.parse('002594') == '002594'
        assert StockCodeParser.parse('300750') == '300750'

    def test_parse_6digit_sh_code(self):
        """测试上交所6位代码"""
        assert StockCodeParser.parse('600000') == '600000'
        assert StockCodeParser.parse('688981') == '688981'
        assert StockCodeParser.parse('600519') == '600519'

    def test_parse_full_code(self):
        """测试完整代码格式"""
        assert StockCodeParser.parse('000001.SZ') == '000001'
        assert StockCodeParser.parse('600000.SS') == '600000'
        assert StockCodeParser.parse('000001.sz') == '000001'
        assert StockCodeParser.parse('600000.ss') == '600000'

    def test_parse_chinese_name(self):
        """测试中文名称"""
        assert StockCodeParser.parse('平安银行') == '000001'
        assert StockCodeParser.parse('贵州茅台') == '600519'
        assert StockCodeParser.parse('招商银行') == '600036'

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

    def test_get_exchange(self):
        """测试获取交易所"""
        assert StockCodeParser.get_exchange('000001') == 'sz'
        assert StockCodeParser.get_exchange('600000') == 'sh'
        assert StockCodeParser.get_exchange('688981') == 'sh'
        assert StockCodeParser.get_exchange('300750') == 'sz'

    def test_get_standard_code(self):
        """测试获取标准代码"""
        assert StockCodeParser.get_standard_code('000001') == '000001.SZ'  # 深交所
        assert StockCodeParser.get_standard_code('600000') == '600000.SH'  # 上交所
        assert StockCodeParser.get_standard_code('002594') == '002594.SZ'  # 深交所

    def test_get_stock_name(self):
        """测试获取股票名称"""
        assert StockCodeParser.get_stock_name('000001') == '平安银行'
        assert StockCodeParser.get_stock_name('600519') == '贵州茅台'
        assert StockCodeParser.get_stock_name('999999') == '未知'


class TestDataFetcher:
    """测试数据获取类"""

    def test_init(self):
        """测试初始化"""
        fetcher = DataFetcher()
        assert fetcher.MAX_RETRIES == 3
        assert fetcher.RETRY_INTERVAL == 2

    def test_process_data(self):
        """测试数据处理"""
        fetcher = DataFetcher()

        # 创建测试数据
        df = pd.DataFrame({
            '日期': ['20240101', '20240102', '20240103'] * 10,
            '开盘': [10.0] * 30,
            '最高': [10.5] * 30,
            '最低': [9.5] * 30,
            '收盘': [10.2] * 30,
            '成交量': [1000000] * 30
        })

        processed = fetcher._process_data(df)

        assert 'trade_date' in processed.columns
        assert 'close' in processed.columns
        assert len(processed) == 30
        # 验证日期是升序排列
        assert processed['trade_date'].is_monotonic_increasing