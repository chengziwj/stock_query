"""量价关系分析模块 - 成交量与价格关系分析"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import numpy as np


class VolumePricePattern(Enum):
    """量价形态"""
    HEALTHY_UP = "价升量增"        # 健康上涨
    WEAK_UP = "价升量缩"           # 上涨乏力
    PANIC_DOWN = "价跌量增"        # 恐慌抛售
    RELIEF_DOWN = "价跌量缩"       # 卖压减轻
    TOP_DIVERGENCE = "顶背离"      # 价涨量缩（顶部信号）
    BOTTOM_DIVERGENCE = "底背离"   # 价跌量缩（底部信号）
    VOLUME_BREAKOUT = "放量突破"   # 放量突破
    VOLUME_BREAKDOWN = "放量下跌"  # 放量下跌
    CONSOLIDATION = "缩量盘整"     # 缩量盘整


@dataclass
class VolumePriceSignal:
    """量价信号"""
    pattern: VolumePricePattern
    signal: str  # bullish / bearish / neutral
    strength: int  # 1-5
    description: str


def calculate_volume_ratio(df: pd.DataFrame, period: int = 5) -> pd.Series:
    """
    计算量比

    量比 = 当日成交量 / N日平均成交量

    Args:
        df: 包含 'vol' 列的DataFrame
        period: 均量周期

    Returns:
        量比Series
    """
    vol_ma = df['vol'].rolling(window=period).mean()
    volume_ratio = df['vol'] / vol_ma
    return volume_ratio


def calculate_obv_trend(df: pd.DataFrame, period: int = 5) -> pd.Series:
    """
    计算OBV趋势

    Args:
        df: 包含 'close', 'vol' 列的DataFrame
        period: 计算周期

    Returns:
        OBV变化率Series
    """
    close = df['close']
    volume = df['vol']

    direction = np.where(close > close.shift(1), 1,
                         np.where(close < close.shift(1), -1, 0))

    obv = (volume * direction).cumsum()
    obv_change = obv.pct_change(period)

    return obv_change


def detect_volume_price_pattern(df: pd.DataFrame, lookback: int = 5) -> VolumePriceSignal:
    """
    检测量价形态

    Args:
        df: 包含 'close', 'vol' 列的DataFrame
        lookback: 回看天数

    Returns:
        量价信号
    """
    close = df['close']
    vol = df['vol']

    # 计算近期价格和成交量变化
    price_change = (close.iloc[-1] - close.iloc[-lookback]) / close.iloc[-lookback] * 100
    vol_ma = vol.rolling(window=lookback).mean().iloc[-1]
    current_vol = vol.iloc[-1]
    vol_ratio = current_vol / vol_ma if vol_ma > 0 else 1

    # 价格趋势
    price_trend_up = close.iloc[-1] > close.iloc[-lookback]

    # 成交量趋势
    vol_trend_up = current_vol > vol.iloc[-lookback]

    # 检测形态
    # 1. 价升量增 - 健康上涨
    if price_change > 2 and vol_ratio > 1.5:
        return VolumePriceSignal(
            pattern=VolumePricePattern.HEALTHY_UP,
            signal="bullish",
            strength=5,
            description=f"价升量增：价格上涨{price_change:.1f}%，成交量放大{vol_ratio:.1f}倍，买盘积极"
        )

    # 2. 价升量缩 - 上涨乏力
    if price_change > 1 and vol_ratio < 0.7:
        return VolumePriceSignal(
            pattern=VolumePricePattern.WEAK_UP,
            signal="bearish",
            strength=4,
            description=f"价升量缩：价格上涨{price_change:.1f}%，但成交量萎缩，上涨动能不足"
        )

    # 3. 价跌量增 - 恐慌抛售
    if price_change < -2 and vol_ratio > 1.5:
        return VolumePriceSignal(
            pattern=VolumePricePattern.PANIC_DOWN,
            signal="bearish",
            strength=5,
            description=f"价跌量增：价格下跌{abs(price_change):.1f}%，成交量放大{vol_ratio:.1f}倍，恐慌抛售"
        )

    # 4. 价跌量缩 - 卖压减轻
    if price_change < -1 and vol_ratio < 0.7:
        return VolumePriceSignal(
            pattern=VolumePricePattern.RELIEF_DOWN,
            signal="bullish",
            strength=3,
            description=f"价跌量缩：价格下跌{abs(price_change):.1f}%，成交量萎缩，卖压减轻"
        )

    # 5. 放量突破（价格突破近期高点）
    recent_high = close.iloc[-lookback:-1].max()
    if close.iloc[-1] > recent_high and vol_ratio > 1.5:
        return VolumePriceSignal(
            pattern=VolumePricePattern.VOLUME_BREAKOUT,
            signal="bullish",
            strength=5,
            description=f"放量突破：突破近期高点{recent_high:.2f}，成交量放大{vol_ratio:.1f}倍"
        )

    # 6. 放量下跌（价格跌破近期低点）
    recent_low = close.iloc[-lookback:-1].min()
    if close.iloc[-1] < recent_low and vol_ratio > 1.5:
        return VolumePriceSignal(
            pattern=VolumePricePattern.VOLUME_BREAKDOWN,
            signal="bearish",
            strength=5,
            description=f"放量下跌：跌破近期低点{recent_low:.2f}，成交量放大{vol_ratio:.1f}倍"
        )

    # 7. 缩量盘整
    if abs(price_change) < 2 and vol_ratio < 0.7:
        return VolumePriceSignal(
            pattern=VolumePricePattern.CONSOLIDATION,
            signal="neutral",
            strength=2,
            description=f"缩量盘整：价格波动{abs(price_change):.1f}%，成交量萎缩，等待方向选择"
        )

    # 默认
    return VolumePriceSignal(
        pattern=VolumePricePattern.CONSOLIDATION,
        signal="neutral",
        strength=2,
        description=f"量价关系：价格变化{price_change:.1f}%，量比{vol_ratio:.2f}"
    )


def detect_divergence(df: pd.DataFrame, indicators: Dict, period: int = 10) -> Dict:
    """
    检测量价背离

    Args:
        df: 原始数据
        indicators: 技术指标字典
        period: 检测周期

    Returns:
        背离检测结果
    """
    divergences = []

    close = df['close']
    obv = indicators['obv']

    # 检测顶背离：价格创新高但OBV没创新高
    if len(close) >= period:
        recent_close = close.iloc[-period:]
        recent_obv = obv.iloc[-period:]

        # 价格创新高
        if close.iloc[-1] == recent_close.max():
            # OBV没创新高
            if recent_obv.iloc[-1] < recent_obv.max() * 0.95:
                divergences.append({
                    'type': '顶背离',
                    'signal': 'bearish',
                    'description': '价格创新高但OBV未创新高，顶背离信号，警惕回调'
                })

        # 价格创新低
        if close.iloc[-1] == recent_close.min():
            # OBV没创新低
            if recent_obv.iloc[-1] > recent_obv.min() * 1.05:
                divergences.append({
                    'type': '底背离',
                    'signal': 'bullish',
                    'description': '价格创新低但OBV未创新低，底背离信号，可能反弹'
                })

    return divergences


def analyze_money_flow(df: pd.DataFrame, period: int = 5) -> Dict:
    """
    分析资金流向

    Args:
        df: 包含 'close', 'high', 'low', 'vol' 列的DataFrame
        period: 分析周期

    Returns:
        资金流向分析结果
    """
    close = df['close']
    high = df['high']
    low = df['low']
    vol = df['vol']

    # 计算典型价格
    typical_price = (high + low + close) / 3

    # 计算资金流量
    money_flow = typical_price * vol

    # 正负资金流量
    positive_mf = pd.Series(np.where(typical_price > typical_price.shift(1), money_flow, 0), index=df.index)
    negative_mf = pd.Series(np.where(typical_price < typical_price.shift(1), money_flow, 0), index=df.index)

    # 资金流量比率
    positive_sum = positive_mf.rolling(window=period).sum().iloc[-1]
    negative_sum = negative_mf.rolling(window=period).sum().iloc[-1]

    if negative_sum == 0:
        mfi_ratio = 100
    else:
        mfi_ratio = 100 - 100 / (1 + positive_sum / negative_sum)

    # 资金净流入
    net_inflow = positive_sum - negative_sum
    total_flow = positive_sum + negative_sum

    if total_flow > 0:
        net_inflow_pct = net_inflow / total_flow * 100
    else:
        net_inflow_pct = 0

    # 判断资金流向
    if net_inflow_pct > 20:
        flow_status = "资金大幅流入"
        flow_signal = "bullish"
    elif net_inflow_pct > 5:
        flow_status = "资金小幅流入"
        flow_signal = "bullish"
    elif net_inflow_pct < -20:
        flow_status = "资金大幅流出"
        flow_signal = "bearish"
    elif net_inflow_pct < -5:
        flow_status = "资金小幅流出"
        flow_signal = "bearish"
    else:
        flow_status = "资金平衡"
        flow_signal = "neutral"

    return {
        'mfi': round(mfi_ratio, 2),
        'net_inflow_pct': round(net_inflow_pct, 2),
        'flow_status': flow_status,
        'flow_signal': flow_signal,
        'positive_flow': round(positive_sum / 100000000, 2),  # 亿元
        'negative_flow': round(negative_sum / 100000000, 2),
    }


def get_volume_price_analysis(df: pd.DataFrame, indicators: Dict) -> Dict:
    """
    获取完整的量价分析

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        量价分析结果
    """
    # 量价形态
    vp_signal = detect_volume_price_pattern(df)

    # 背离检测
    divergences = detect_divergence(df, indicators)

    # 资金流向
    money_flow = analyze_money_flow(df)

    # 量比
    vol_ratio = calculate_volume_ratio(df).iloc[-1]

    # 成交量趋势
    vol_ma5 = df['vol'].rolling(window=5).mean().iloc[-1]
    vol_ma10 = df['vol'].rolling(window=10).mean().iloc[-1]
    vol_trend = "放量" if vol_ma5 > vol_ma10 else "缩量"

    return {
        'pattern': vp_signal.pattern.value,
        'signal': vp_signal.signal,
        'strength': vp_signal.strength,
        'description': vp_signal.description,
        'volume_ratio': round(vol_ratio, 2),
        'volume_trend': vol_trend,
        'divergences': divergences,
        'money_flow': money_flow
    }