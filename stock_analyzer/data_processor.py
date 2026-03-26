"""数据处理模块 - 数据获取、指标计算、特征工程"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

import pandas as pd
import numpy as np

from data_fetcher import fetch_stock_data, StockCodeParser
from technical_indicators import calculate_all_indicators, get_latest_values
from trend_analyzer import get_trend_analysis
from support_resistance import get_support_resistance_analysis
from volume_price import get_volume_price_analysis
from price_prediction import get_price_prediction
from feature_engineering import (
    create_feature_set, get_feature_engineering,
    calculate_returns, calculate_historical_volatility,
    calculate_price_position, calculate_future_returns
)


@dataclass
class PredictionTarget:
    """预测目标"""
    future_1d_return: float      # 未来1日收益率
    future_3d_return: float      # 未来3日收益率
    future_5d_return: float      # 未来5日收益率
    future_1d_direction: int     # 未来1日方向 (1=涨, -1=跌, 0=平)
    future_5d_direction: int     # 未来5日方向


class DataProcessor:
    """
    数据处理类

    整合数据获取、指标计算、特征工程
    """

    def __init__(self, symbol: str = None, months: int = 12):
        """
        初始化数据处理对象

        Args:
            symbol: 股票代码
            months: 获取数据月数（默认12个月）
        """
        self.symbol = symbol
        self.months = months
        self._df = None
        self._indicators = None
        self._latest = None
        self._analysis = None
        self._sr_analysis = None
        self._vp_analysis = None
        self._prediction = None
        self._features = None

    def fetch_data(self, symbol: str = None, months: int = None) -> pd.DataFrame:
        """
        获取股票数据

        Args:
            symbol: 股票代码（可覆盖初始化时的设置）
            months: 数据月数（可覆盖初始化时的设置）

        Returns:
            股票数据DataFrame
        """
        if symbol:
            self.symbol = symbol
        if months:
            self.months = months

        if not self.symbol:
            raise ValueError("请提供股票代码")

        self._df, self._standard_code, self._stock_name = fetch_stock_data(
            self.symbol, self.months
        )

        # 清除缓存
        self._indicators = None
        self._latest = None
        self._analysis = None
        self._sr_analysis = None
        self._vp_analysis = None
        self._prediction = None
        self._features = None

        return self._df

    def calculate_indicators(self, df: pd.DataFrame = None) -> Dict:
        """
        计算所有技术指标

        Args:
            df: 股票数据（可选，如未提供则使用已获取的数据）

        Returns:
            技术指标字典
        """
        if df is not None:
            self._df = df

        if self._df is None:
            raise ValueError("请先获取数据")

        if self._indicators is None:
            self._indicators = calculate_all_indicators(self._df)
            self._latest = get_latest_values(self._indicators, self._df)

        return self._indicators

    def create_features(self, df: pd.DataFrame = None, indicators: Dict = None) -> Dict:
        """
        创建特征工程

        Args:
            df: 股票数据（可选）
            indicators: 技术指标（可选）

        Returns:
            特征字典
        """
        if df is not None:
            self._df = df

        if self._df is None:
            raise ValueError("请先获取数据")

        # 确保指标已计算
        if indicators is not None:
            self._indicators = indicators
        elif self._indicators is None:
            self.calculate_indicators()

        # 确保量价分析已完成
        if self._vp_analysis is None:
            self._vp_analysis = get_volume_price_analysis(self._df, self._indicators)

        if self._features is None:
            self._features = get_feature_engineering(
                self._df, self._indicators, self._vp_analysis
            )

        return self._features

    def analyze(self, symbol: str = None) -> Dict:
        """
        执行完整分析

        Args:
            symbol: 股票代码（可选）

        Returns:
            完整分析结果
        """
        # 获取数据
        if symbol or self._df is None:
            self.fetch_data(symbol)

        # 计算指标
        self.calculate_indicators()

        # 趋势分析
        self._analysis = get_trend_analysis(self._df, self._indicators)

        # 支撑阻力分析
        self._sr_analysis = get_support_resistance_analysis(
            self._df, self._indicators, self._analysis
        )

        # 量价分析
        self._vp_analysis = get_volume_price_analysis(self._df, self._indicators)

        # 价格预测
        self._prediction = get_price_prediction(
            self._df, self._indicators, self._sr_analysis, self._vp_analysis
        )

        # 特征工程
        self._features = self.create_features()

        return {
            'symbol': self._standard_code,
            'name': self._stock_name,
            'data': self._df,
            'indicators': self._indicators,
            'latest': self._latest,
            'analysis': self._analysis,
            'support_resistance': self._sr_analysis,
            'volume_price': self._vp_analysis,
            'prediction': self._prediction,
            'features': self._features
        }

    def get_prediction_targets(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """
        获取预测目标（用于模型训练）

        Args:
            df: 股票数据（可选）

        Returns:
            包含预测目标的DataFrame
        """
        if df is not None:
            self._df = df

        if self._df is None:
            raise ValueError("请先获取数据")

        # 计算未来收益率
        future_returns = calculate_future_returns(self._df, days=[1, 3, 5])

        # 创建目标DataFrame
        targets = pd.DataFrame(index=self._df.index)
        targets['future_1d_return'] = future_returns['future_1d_return']
        targets['future_3d_return'] = future_returns['future_3d_return']
        targets['future_5d_return'] = future_returns['future_5d_return']

        # 方向标签
        targets['future_1d_direction'] = (targets['future_1d_return'] > 0).astype(int)
        targets['future_1d_direction'] = targets['future_1d_direction'].map({1: 1, 0: -1})

        targets['future_5d_direction'] = (targets['future_5d_return'] > 0).astype(int)
        targets['future_5d_direction'] = targets['future_5d_direction'].map({1: 1, 0: -1})

        return targets

    def prepare_training_data(self, symbol: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        准备训练数据

        Args:
            symbol: 股票代码（可选）

        Returns:
            (特征DataFrame, 目标DataFrame)
        """
        # 执行分析
        result = self.analyze(symbol)

        df = result['data']
        indicators = result['indicators']

        # 构建特征DataFrame
        feature_rows = []

        # 为每一天构建特征
        for i in range(60, len(df) - 5):  # 留出MA60计算期和未来5天预测期
            # 截取到当前的数据
            df_slice = df.iloc[:i+1].copy()

            # 计算指标
            inds = calculate_all_indicators(df_slice)

            # 计算特征
            returns = calculate_returns(df_slice)
            volatility = calculate_historical_volatility(df_slice)
            price_pos = calculate_price_position(df_slice)

            row = {
                # 基础特征
                'returns_1d': returns['returns_1d'].iloc[i],
                'returns_5d': returns['returns_5d'].iloc[i],
                'returns_20d': returns['returns_20d'].iloc[i],
                'volatility': volatility.iloc[i],
                'price_position': price_pos.iloc[i],

                # 技术指标
                'rsi': inds['rsi'].iloc[i],
                'kdj_k': inds['kdj']['K'].iloc[i],
                'kdj_d': inds['kdj']['D'].iloc[i],
                'macd': inds['macd']['MACD'].iloc[i],
                'macd_dif': inds['macd']['DIF'].iloc[i],

                # 均线
                'ma5': inds['ma']['MA5'].iloc[i],
                'ma10': inds['ma']['MA10'].iloc[i],
                'ma20': inds['ma']['MA20'].iloc[i],
                'ma60': inds['ma']['MA60'].iloc[i],

                # 布林带
                'boll_upper': inds['bollinger']['upper'].iloc[i],
                'boll_lower': inds['bollinger']['lower'].iloc[i],

                # 成交量
                'obv': inds['obv'].iloc[i],
                'atr': inds['atr'].iloc[i],
                'adx': inds['dmi']['ADX'].iloc[i],

                # 目标
                'target_1d': (df['close'].iloc[i+1] - df['close'].iloc[i]) / df['close'].iloc[i] * 100,
                'target_5d': (df['close'].iloc[i+5] - df['close'].iloc[i]) / df['close'].iloc[i] * 100,
                'target_direction_1d': 1 if df['close'].iloc[i+1] > df['close'].iloc[i] else -1,
                'target_direction_5d': 1 if df['close'].iloc[i+5] > df['close'].iloc[i] else -1
            }

            feature_rows.append(row)

        # 构建DataFrame
        features_df = pd.DataFrame(feature_rows)

        # 分离特征和目标
        target_cols = ['target_1d', 'target_5d', 'target_direction_1d', 'target_direction_5d']
        X = features_df.drop(columns=target_cols)
        y = features_df[target_cols]

        return X, y

    @property
    def data(self) -> pd.DataFrame:
        """获取股票数据"""
        return self._df

    @property
    def indicators(self) -> Dict:
        """获取技术指标"""
        return self._indicators

    @property
    def latest_values(self) -> Dict:
        """获取最新指标值"""
        return self._latest

    @property
    def prediction(self) -> Dict:
        """获取价格预测"""
        return self._prediction


# 便捷函数
def analyze_stock(symbol: str, months: int = 12) -> Dict:
    """
    分析股票（便捷函数）

    Args:
        symbol: 股票代码
        months: 数据月数

    Returns:
        分析结果
    """
    processor = DataProcessor(symbol, months)
    return processor.analyze()