"""特征工程模块 - 构建预测特征"""

from typing import Dict, List, Tuple
from dataclasses import dataclass

import pandas as pd
import numpy as np


@dataclass
class FeatureSet:
    """特征集合"""
    # 基础特征
    returns_1d: float          # 1日收益率
    returns_5d: float          # 5日收益率
    returns_20d: float         # 20日收益率
    volatility: float          # 历史波动率
    price_position: float      # 价格位置（当前价/区间）

    # 趋势特征
    ma_alignment_score: int    # 均线排列得分 (-4 到 4)
    macd_signal: int           # MACD信号 (-1, 0, 1)
    bollinger_position: float  # 布林带位置 (0-1)

    # 动量特征
    rsi_value: float           # RSI值
    kdj_signal: int            # KDJ信号 (-1, 0, 1)
    obv_trend: float           # OBV趋势

    # 量价特征
    volume_ratio: float        # 量比
    volume_price_match: float  # 量价匹配度
    vp_pattern: str            # 量价形态

    # 综合评分
    overbought_score: int      # 超买评分 (0-5)
    oversold_score: int        # 超卖评分 (0-5)
    bullish_score: int         # 看涨信号数
    bearish_score: int         # 看跌信号数

    # 极端信号
    extreme_volume: str        # 极端成交量形态


def calculate_returns(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    计算收益率

    Args:
        df: 包含 'close' 列的DataFrame

    Returns:
        字典包含 'returns_1d', 'returns_5d', 'returns_20d'
    """
    close = df['close']

    return {
        'returns_1d': close.pct_change(1) * 100,
        'returns_5d': close.pct_change(5) * 100,
        'returns_20d': close.pct_change(20) * 100
    }


def calculate_historical_volatility(df: pd.DataFrame, period: int = 20) -> pd.Series:
    """
    计算历史波动率（年化）

    Args:
        df: 包含 'close' 列的DataFrame
        period: 计算周期

    Returns:
        历史波动率Series
    """
    close = df['close']
    log_returns = np.log(close / close.shift(1))

    # 计算标准差并年化（假设252个交易日）
    volatility = log_returns.rolling(window=period).std() * np.sqrt(252) * 100

    return volatility


def calculate_price_position(df: pd.DataFrame, period: int = 60) -> pd.Series:
    """
    计算价格位置

    价格位置 = (当前价 - 最低价) / (最高价 - 最低价)
    0表示在最低点，1表示在最高点

    Args:
        df: 包含 'close', 'high', 'low' 列的DataFrame
        period: 计算周期

    Returns:
        价格位置Series (0-1)
    """
    close = df['close']
    high = df['high'].rolling(window=period).max()
    low = df['low'].rolling(window=period).min()

    position = (close - low) / (high - low)
    return position.fillna(0.5)


def calculate_ma_alignment_score(indicators: Dict) -> int:
    """
    计算均线排列得分

    得分范围：-4 到 4
    - 4: 完美多头排列 (MA5 > MA10 > MA20 > MA60)
    - -4: 完美空头排列 (MA5 < MA10 < MA20 < MA60)

    Args:
        indicators: 技术指标字典

    Returns:
        均线排列得分
    """
    ma5 = indicators['ma']['MA5'].iloc[-1]
    ma10 = indicators['ma']['MA10'].iloc[-1]
    ma20 = indicators['ma']['MA20'].iloc[-1]
    ma60 = indicators['ma']['MA60'].iloc[-1]

    if pd.isna(ma60):
        return 0

    score = 0

    # MA5 vs MA10
    if ma5 > ma10:
        score += 1
    elif ma5 < ma10:
        score -= 1

    # MA10 vs MA20
    if ma10 > ma20:
        score += 1
    elif ma10 < ma20:
        score -= 1

    # MA20 vs MA60
    if ma20 > ma60:
        score += 1
    elif ma20 < ma60:
        score -= 1

    # 价格与MA5的关系需要从原始数据判断
    # 这里简化处理，只比较均线关系

    return score


def calculate_bollinger_position(df: pd.DataFrame, indicators: Dict) -> float:
    """
    计算价格在布林带中的位置

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        位置值 (0-1, 0=下轨, 0.5=中轨, 1=上轨)
    """
    close = df['close'].iloc[-1]
    upper = indicators['bollinger']['upper'].iloc[-1]
    lower = indicators['bollinger']['lower'].iloc[-1]

    if pd.isna(upper) or pd.isna(lower):
        return 0.5

    band_width = upper - lower
    if band_width <= 0:
        return 0.5

    position = (close - lower) / band_width
    return max(0, min(1, position))


def calculate_volume_price_correlation(df: pd.DataFrame, period: int = 20) -> float:
    """
    计算量价相关系数

    Args:
        df: 包含 'close', 'vol' 列的DataFrame
        period: 计算周期

    Returns:
        相关系数 (-1 到 1)
    """
    close = df['close'].iloc[-period:]
    vol = df['vol'].iloc[-period:]

    if len(close) < period:
        return 0

    correlation = close.corr(vol)
    return correlation if not pd.isna(correlation) else 0


def calculate_overbought_score(indicators: Dict) -> int:
    """
    计算超买评分

    检查多个指标是否处于超买状态

    Args:
        indicators: 技术指标字典

    Returns:
        超买评分 (0-5)
    """
    score = 0

    # RSI超买
    rsi = indicators['rsi'].iloc[-1]
    if not pd.isna(rsi):
        if rsi > 80:
            score += 2
        elif rsi > 70:
            score += 1

    # KDJ超买
    kdj_k = indicators['kdj']['K'].iloc[-1]
    kdj_d = indicators['kdj']['D'].iloc[-1]
    if not pd.isna(kdj_k):
        if kdj_k > 80 and kdj_d > 80:
            score += 1

    # KDJ J值超买
    kdj_j = indicators['kdj']['J'].iloc[-1]
    if not pd.isna(kdj_j) and kdj_j > 100:
        score += 1

    # WR超买
    wr = indicators['wr'].iloc[-1]
    if not pd.isna(wr) and wr < -80:
        score += 1

    return score


def calculate_oversold_score(indicators: Dict) -> int:
    """
    计算超卖评分

    检查多个指标是否处于超卖状态

    Args:
        indicators: 技术指标字典

    Returns:
        超卖评分 (0-5)
    """
    score = 0

    # RSI超卖
    rsi = indicators['rsi'].iloc[-1]
    if not pd.isna(rsi):
        if rsi < 20:
            score += 2
        elif rsi < 30:
            score += 1

    # KDJ超卖
    kdj_k = indicators['kdj']['K'].iloc[-1]
    kdj_d = indicators['kdj']['D'].iloc[-1]
    if not pd.isna(kdj_k):
        if kdj_k < 20 and kdj_d < 20:
            score += 1

    # KDJ J值超卖
    kdj_j = indicators['kdj']['J'].iloc[-1]
    if not pd.isna(kdj_j) and kdj_j < 0:
        score += 1

    # WR超卖
    wr = indicators['wr'].iloc[-1]
    if not pd.isna(wr) and wr > -20:
        score += 1

    return score


def estimate_buy_sell_pressure(df: pd.DataFrame, period: int = 5) -> Dict:
    """
    估算主动买卖盘

    使用收盘价在当日最高最低价的位置来估算

    Args:
        df: 包含 'open', 'high', 'low', 'close', 'vol' 列的DataFrame
        period: 计算周期

    Returns:
        包含主动买入/卖出估算的字典
    """
    high = df['high']
    low = df['low']
    close = df['close']
    vol = df['vol']

    # 计算当日收盘价位置
    day_range = high - low
    day_range = day_range.replace(0, 0.01)  # 避免除零

    close_position = (close - low) / day_range

    # 估算主动买入量 = 收盘位置 * 成交量
    # 估算主动卖出量 = (1 - 收盘位置) * 成交量
    buy_volume = close_position * vol
    sell_volume = (1 - close_position) * vol

    # 近期累计
    total_buy = buy_volume.iloc[-period:].sum()
    total_sell = sell_volume.iloc[-period:].sum()
    total_vol = vol.iloc[-period:].sum()

    # 净买入比例
    net_buy_ratio = (total_buy - total_sell) / total_vol if total_vol > 0 else 0

    return {
        'buy_volume': round(total_buy / 100000000, 2),  # 亿股
        'sell_volume': round(total_sell / 100000000, 2),
        'net_buy_ratio': round(net_buy_ratio * 100, 2),  # 百分比
        'pressure': "买盘占优" if net_buy_ratio > 0.1 else "卖盘占优" if net_buy_ratio < -0.1 else "买卖平衡"
    }


def calculate_future_returns(df: pd.DataFrame, days: List[int] = [1, 3, 5]) -> Dict[str, pd.Series]:
    """
    计算未来N日收益率（用于训练预测模型）

    Args:
        df: 包含 'close' 列的DataFrame
        days: 预测天数列表

    Returns:
        字典包含各天数的未来收益率
    """
    close = df['close']
    result = {}

    for day in days:
        future_return = (close.shift(-day) - close) / close * 100
        result[f'future_{day}d_return'] = future_return

    return result


def create_feature_set(df: pd.DataFrame, indicators: Dict, vp_analysis: Dict) -> FeatureSet:
    """
    创建完整的特征集合

    Args:
        df: 原始数据
        indicators: 技术指标字典
        vp_analysis: 量价分析结果

    Returns:
        FeatureSet对象
    """
    last_idx = len(df) - 1

    # 计算收益率
    returns = calculate_returns(df)

    # 计算历史波动率
    volatility = calculate_historical_volatility(df)

    # 计算价格位置
    price_position = calculate_price_position(df)

    # 量价相关系数
    vp_corr = calculate_volume_price_correlation(df)

    # 买卖盘估算
    buy_sell = estimate_buy_sell_pressure(df)

    return FeatureSet(
        returns_1d=round(returns['returns_1d'].iloc[last_idx], 2) if not pd.isna(returns['returns_1d'].iloc[last_idx]) else 0,
        returns_5d=round(returns['returns_5d'].iloc[last_idx], 2) if not pd.isna(returns['returns_5d'].iloc[last_idx]) else 0,
        returns_20d=round(returns['returns_20d'].iloc[last_idx], 2) if not pd.isna(returns['returns_20d'].iloc[last_idx]) else 0,
        volatility=round(volatility.iloc[last_idx], 2) if not pd.isna(volatility.iloc[last_idx]) else 0,
        price_position=round(price_position.iloc[last_idx], 2) if not pd.isna(price_position.iloc[last_idx]) else 0.5,
        ma_alignment_score=calculate_ma_alignment_score(indicators),
        macd_signal=1 if indicators['macd']['MACD'].iloc[last_idx] > 0 else -1,
        bollinger_position=round(calculate_bollinger_position(df, indicators), 2),
        rsi_value=round(indicators['rsi'].iloc[last_idx], 1),
        kdj_signal=1 if indicators['kdj']['K'].iloc[last_idx] > indicators['kdj']['D'].iloc[last_idx] else -1,
        obv_trend=round(vp_analysis['money_flow']['net_inflow_pct'], 1),
        volume_ratio=vp_analysis['volume_ratio'],
        volume_price_match=round(vp_corr, 2),
        vp_pattern=vp_analysis['pattern'],
        overbought_score=calculate_overbought_score(indicators),
        oversold_score=calculate_oversold_score(indicators),
        bullish_score=sum([
            1 for s in [indicators['rsi'].iloc[last_idx] > 50,
                       indicators['kdj']['K'].iloc[last_idx] > indicators['kdj']['D'].iloc[last_idx],
                       indicators['macd']['MACD'].iloc[last_idx] > 0]
            if s
        ]),
        bearish_score=sum([
            1 for s in [indicators['rsi'].iloc[last_idx] < 50,
                       indicators['kdj']['K'].iloc[last_idx] < indicators['kdj']['D'].iloc[last_idx],
                       indicators['macd']['MACD'].iloc[last_idx] < 0]
            if s
        ]),
        extreme_volume=vp_analysis.get('extreme_volume', {}).get('pattern', '')
    )


def get_feature_engineering(df: pd.DataFrame, indicators: Dict, vp_analysis: Dict) -> Dict:
    """
    获取完整的特征工程结果

    Args:
        df: 原始数据
        indicators: 技术指标字典
        vp_analysis: 量价分析结果

    Returns:
        特征工程结果字典
    """
    feature_set = create_feature_set(df, indicators, vp_analysis)

    # 买卖盘估算
    buy_sell = estimate_buy_sell_pressure(df)

    return {
        'features': {
            'returns': {
                '1d': feature_set.returns_1d,
                '5d': feature_set.returns_5d,
                '20d': feature_set.returns_20d
            },
            'volatility': feature_set.volatility,
            'price_position': feature_set.price_position,
            'trend': {
                'ma_alignment_score': feature_set.ma_alignment_score,
                'macd_signal': feature_set.macd_signal,
                'bollinger_position': feature_set.bollinger_position
            },
            'momentum': {
                'rsi': feature_set.rsi_value,
                'kdj_signal': feature_set.kdj_signal,
                'obv_trend': feature_set.obv_trend
            },
            'volume_price': {
                'volume_ratio': feature_set.volume_ratio,
                'vp_correlation': feature_set.volume_price_match,
                'pattern': feature_set.vp_pattern,
                'buy_sell_pressure': buy_sell,
                'extreme_volume': feature_set.extreme_volume
            },
            'scores': {
                'overbought': feature_set.overbought_score,
                'oversold': feature_set.oversold_score,
                'bullish': feature_set.bullish_score,
                'bearish': feature_set.bearish_score
            }
        },
        'feature_set': feature_set
    }