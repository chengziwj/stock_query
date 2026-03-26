"""筛选器测试"""
import pytest
from stock_screener import StockScreener


class TestStockScreener:
    """测试股票筛选器"""

    def test_init(self):
        """测试初始化"""
        screener = StockScreener()
        assert screener is not None

    def test_filter_st_stocks(self):
        """测试ST股票过滤"""
        screener = StockScreener()
        stocks = ['000001', '000002', 'ST0001', '600000']
        filtered = screener._filter_st_stocks(stocks)
        assert 'ST0001' not in filtered
        assert len(filtered) == 3

    def test_filter_by_market_cap(self):
        """测试市值过滤"""
        screener = StockScreener(min_market_cap=50)
        # 模拟市值数据
        result = screener._filter_by_market_cap(['000001', '000002'])
        assert isinstance(result, list)
