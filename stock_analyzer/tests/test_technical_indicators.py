"""测试技术指标计算模块"""

import pytest
import pandas as pd
import numpy as np

from technical_indicators import (
    calculate_ma,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_all_indicators,
    get_latest_values
)


@pytest.fixture
def sample_data():
    """创建测试数据"""
    np.random.seed(42)
    n = 100

    # 生成模拟价格数据
    dates = pd.date_range('2024-01-01', periods=n, freq='D')
    close = 100 + np.cumsum(np.random.randn(n) * 2)
    open_price = close + np.random.randn(n) * 0.5
    high = close + np.abs(np.random.randn(n) * 1)
    low = close - np.abs(np.random.randn(n) * 1)
    vol = np.random.randint(1000000, 5000000, n)

    df = pd.DataFrame({
        'trade_date': dates,
        'open': open_price,
        'high': high,
        'low': low,
        'close': close,
        'vol': vol
    })

    return df


class TestCalculateMA:
    """测试MA计算"""

    def test_ma5(self, sample_data):
        """测试MA5计算"""
        ma = calculate_ma(sample_data, periods=(5,))
        assert 'MA5' in ma
        # 手动验证第5个点
        expected = sample_data['close'].iloc[:5].mean()
        assert np.isclose(ma['MA5'].iloc[4], expected)

    def test_ma20(self, sample_data):
        """测试MA20计算"""
        ma = calculate_ma(sample_data, periods=(20,))
        assert 'MA20' in ma
        # 前19个值应该是NaN
        assert pd.isna(ma['MA20'].iloc[18])
        assert not pd.isna(ma['MA20'].iloc[19])

    def test_ma60(self, sample_data):
        """测试MA60计算"""
        ma = calculate_ma(sample_data, periods=(60,))
        assert 'MA60' in ma
        # 前59个值应该是NaN
        assert pd.isna(ma['MA60'].iloc[58])
        assert not pd.isna(ma['MA60'].iloc[59])

    def test_default_periods(self, sample_data):
        """测试默认周期"""
        ma = calculate_ma(sample_data)
        assert 'MA5' in ma
        assert 'MA20' in ma
        assert 'MA60' in ma


class TestCalculateRSI:
    """测试RSI计算"""

    def test_rsi_values(self, sample_data):
        """测试RSI值范围"""
        rsi = calculate_rsi(sample_data)
        # RSI应该在0-100之间
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    def test_rsi_constant_price(self):
        """测试价格不变时RSI"""
        df = pd.DataFrame({
            'close': [100.0] * 50
        })
        rsi = calculate_rsi(df)
        # 价格不变时RSI应该接近50
        assert rsi.iloc[-1] == 50.0

    def test_rsi_upward_trend(self):
        """测试上涨趋势RSI"""
        df = pd.DataFrame({
            'close': range(100, 150)  # 持续上涨
        })
        rsi = calculate_rsi(df)
        # 上涨趋势RSI应该较高
        assert rsi.iloc[-1] > 50


class TestCalculateMACD:
    """测试MACD计算"""

    def test_macd_components(self, sample_data):
        """测试MACD各组件"""
        macd = calculate_macd(sample_data)
        assert 'DIF' in macd
        assert 'DEA' in macd
        assert 'MACD' in macd

    def test_macd_formula(self, sample_data):
        """测试MACD公式"""
        macd = calculate_macd(sample_data)
        # MACD = (DIF - DEA) * 2
        expected = (macd['DIF'] - macd['DEA']) * 2
        assert np.allclose(macd['MACD'].dropna(), expected.dropna())


class TestCalculateBollingerBands:
    """测试布林带计算"""

    def test_bollinger_components(self, sample_data):
        """测试布林带各组件"""
        bb = calculate_bollinger_bands(sample_data)
        assert 'upper' in bb
        assert 'middle' in bb
        assert 'lower' in bb

    def test_bollinger_middle_is_ma20(self, sample_data):
        """测试中轨等于MA20"""
        bb = calculate_bollinger_bands(sample_data)
        ma20 = sample_data['close'].rolling(window=20).mean()
        assert np.allclose(bb['middle'].dropna(), ma20.dropna())

    def test_bollinger_upper_greater_than_lower(self, sample_data):
        """测试上轨大于下轨"""
        bb = calculate_bollinger_bands(sample_data)
        valid_mask = ~(bb['upper'].isna() | bb['lower'].isna())
        assert (bb['upper'][valid_mask] > bb['lower'][valid_mask]).all()


class TestCalculateAllIndicators:
    """测试计算所有指标"""

    def test_all_indicators_present(self, sample_data):
        """测试所有指标都存在"""
        indicators = calculate_all_indicators(sample_data)
        assert 'ma' in indicators
        assert 'rsi' in indicators
        assert 'macd' in indicators
        assert 'bollinger' in indicators


class TestGetLatestValues:
    """测试获取最新值"""

    def test_latest_values_structure(self, sample_data):
        """测试最新值结构"""
        indicators = calculate_all_indicators(sample_data)
        latest = get_latest_values(indicators, sample_data)

        assert 'ma' in latest
        assert 'rsi' in latest
        assert 'macd' in latest
        assert 'bollinger' in latest

        assert 'MA5' in latest['ma']
        assert 'MA20' in latest['ma']
        assert 'MA60' in latest['ma']

    def test_latest_values_are_numbers(self, sample_data):
        """测试最新值是数字"""
        indicators = calculate_all_indicators(sample_data)
        latest = get_latest_values(indicators, sample_data)

        assert isinstance(latest['rsi'], (int, float))
        assert isinstance(latest['macd']['DIF'], (int, float))