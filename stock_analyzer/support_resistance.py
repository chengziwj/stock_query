"""支撑位/阻力位分析模块 - 识别关键价格位和买入建议"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np


@dataclass
class PriceLevel:
    """价格位"""
    price: float
    level_type: str
    strength: int  # 1-5, 5最强
    description: str


@dataclass
class BuySuggestion:
    """买入建议"""
    price: float
    reason: str
    risk_level: str  # 低/中/高
    stop_loss: Optional[float]
    target_price: Optional[float]


def find_swing_lows(df: pd.DataFrame, window: int = 5) -> List[Tuple[int, float]]:
    """
    寻找波段低点

    Args:
        df: 包含 'low' 列的DataFrame
        window: 左右窗口大小

    Returns:
        [(索引, 价格)] 列表
    """
    lows = []
    low_series = df['low'].values

    for i in range(window, len(low_series) - window):
        # 检查是否为局部最小值
        is_low = True
        for j in range(-window, window + 1):
            if j != 0 and low_series[i + j] < low_series[i]:
                is_low = False
                break
        if is_low:
            lows.append((i, low_series[i]))

    return lows


def find_swing_highs(df: pd.DataFrame, window: int = 5) -> List[Tuple[int, float]]:
    """
    寻找波段高点

    Args:
        df: 包含 'high' 列的DataFrame
        window: 左右窗口大小

    Returns:
        [(索引, 价格)] 列表
    """
    highs = []
    high_series = df['high'].values

    for i in range(window, len(high_series) - window):
        # 检查是否为局部最大值
        is_high = True
        for j in range(-window, window + 1):
            if j != 0 and high_series[i + j] > high_series[i]:
                is_high = False
                break
        if is_high:
            highs.append((i, high_series[i]))

    return highs


def find_volume_support(df: pd.DataFrame, bins: int = 20) -> List[Tuple[float, float]]:
    """
    寻找成交量密集区（支撑/阻力区）

    Args:
        df: 包含 'close', 'vol' 列的DataFrame
        bins: 价格区间数量

    Returns:
        [(价格区中点, 成交量)] 列表，按成交量降序
    """
    close = df['close'].values
    vol = df['vol'].values

    # 创建价格区间
    price_min, price_max = close.min(), close.max()
    price_range = price_max - price_min
    bin_width = price_range / bins

    volume_by_price = {}

    for i in range(len(close)):
        bin_idx = int((close[i] - price_min) / bin_width)
        bin_idx = min(bin_idx, bins - 1)
        bin_mid = price_min + (bin_idx + 0.5) * bin_width

        if bin_mid not in volume_by_price:
            volume_by_price[bin_mid] = 0
        volume_by_price[bin_mid] += vol[i]

    # 按成交量排序
    sorted_volumes = sorted(volume_by_price.items(), key=lambda x: x[1], reverse=True)

    return sorted_volumes


def calculate_fibonacci_levels(df: pd.DataFrame) -> Dict[str, float]:
    """
    计算黄金分割位

    Args:
        df: 包含 'high', 'low' 列的DataFrame

    Returns:
        黄金分割位字典
    """
    high = df['high'].max()
    low = df['low'].min()
    diff = high - low

    return {
        'high': high,
        'fib_0.236': high - diff * 0.236,
        'fib_0.382': high - diff * 0.382,
        'fib_0.5': high - diff * 0.5,
        'fib_0.618': high - diff * 0.618,
        'fib_0.786': high - diff * 0.786,
        'low': low
    }


def identify_support_levels(
    df: pd.DataFrame,
    indicators: Dict,
    current_price: float
) -> List[PriceLevel]:
    """
    识别支撑位

    Args:
        df: 原始数据
        indicators: 技术指标字典
        current_price: 当前价格

    Returns:
        支撑位列表（按价格降序）
    """
    supports = []

    # 1. 布林带下轨
    lower_band = indicators['bollinger']['lower'].iloc[-1]
    if not pd.isna(lower_band) and lower_band < current_price:
        supports.append(PriceLevel(
            price=round(lower_band, 2),
            level_type="布林带下轨",
            strength=3,
            description=f"布林带下轨支撑"
        ))

    # 2. MA均线支撑
    ma20 = indicators['ma']['MA20'].iloc[-1]
    ma60 = indicators['ma']['MA60'].iloc[-1]

    if not pd.isna(ma20) and ma20 < current_price:
        supports.append(PriceLevel(
            price=round(ma20, 2),
            level_type="MA20",
            strength=4,
            description="MA20均线支撑"
        ))

    if not pd.isna(ma60) and ma60 < current_price:
        supports.append(PriceLevel(
            price=round(ma60, 2),
            level_type="MA60",
            strength=5,
            description="MA60均线支撑（较强）"
        ))

    # 3. 前期低点支撑
    swing_lows = find_swing_lows(df)
    recent_lows = sorted(swing_lows, key=lambda x: x[0], reverse=True)[:5]  # 最近5个低点

    for idx, price in recent_lows:
        if price < current_price:
            # 计算距离当前的价格差
            distance_pct = (current_price - price) / current_price * 100

            # 根据距离判断强度
            if distance_pct < 5:
                strength = 5
            elif distance_pct < 10:
                strength = 4
            elif distance_pct < 15:
                strength = 3
            else:
                strength = 2

            supports.append(PriceLevel(
                price=round(price, 2),
                level_type="前期低点",
                strength=strength,
                description=f"前期低点支撑（{df['trade_date'].iloc[idx].strftime('%Y-%m-%d')}）"
            ))

    # 4. 黄金分割支撑位
    fib_levels = calculate_fibonacci_levels(df)
    for name, price in fib_levels.items():
        if name.startswith('fib') and price < current_price:
            supports.append(PriceLevel(
                price=round(price, 2),
                level_type=f"黄金分割{name.split('_')[1]}",
                strength=3,
                description=f"黄金分割{name.split('_')[1]}支撑"
            ))

    # 5. 成交量密集区支撑
    volume_zones = find_volume_support(df)
    # 取成交量前3的区域
    for price, vol in volume_zones[:3]:
        if price < current_price:
            supports.append(PriceLevel(
                price=round(price, 2),
                level_type="成交量密集区",
                strength=4,
                description="成交量密集支撑区"
            ))
            break  # 只取最近的

    # 去重并排序（按价格降序）
    seen_prices = set()
    unique_supports = []
    for s in sorted(supports, key=lambda x: x.price, reverse=True):
        key = round(s.price, 2)
        if key not in seen_prices:
            seen_prices.add(key)
            unique_supports.append(s)

    return unique_supports


def identify_resistance_levels(
    df: pd.DataFrame,
    indicators: Dict,
    current_price: float
) -> List[PriceLevel]:
    """
    识别阻力位

    Args:
        df: 原始数据
        indicators: 技术指标字典
        current_price: 当前价格

    Returns:
        阻力位列表（按价格升序）
    """
    resistances = []

    # 1. 布林带上轨
    upper_band = indicators['bollinger']['upper'].iloc[-1]
    if not pd.isna(upper_band) and upper_band > current_price:
        resistances.append(PriceLevel(
            price=round(upper_band, 2),
            level_type="布林带上轨",
            strength=3,
            description="布林带上轨阻力"
        ))

    # 2. MA均线阻力
    ma20 = indicators['ma']['MA20'].iloc[-1]
    ma60 = indicators['ma']['MA60'].iloc[-1]

    if not pd.isna(ma20) and ma20 > current_price:
        resistances.append(PriceLevel(
            price=round(ma20, 2),
            level_type="MA20",
            strength=4,
            description="MA20均线阻力"
        ))

    if not pd.isna(ma60) and ma60 > current_price:
        resistances.append(PriceLevel(
            price=round(ma60, 2),
            level_type="MA60",
            strength=5,
            description="MA60均线阻力（较强）"
        ))

    # 3. 前期高点阻力
    swing_highs = find_swing_highs(df)
    recent_highs = sorted(swing_highs, key=lambda x: x[0], reverse=True)[:5]

    for idx, price in recent_highs:
        if price > current_price:
            distance_pct = (price - current_price) / current_price * 100

            if distance_pct < 5:
                strength = 5
            elif distance_pct < 10:
                strength = 4
            elif distance_pct < 15:
                strength = 3
            else:
                strength = 2

            resistances.append(PriceLevel(
                price=round(price, 2),
                level_type="前期高点",
                strength=strength,
                description=f"前期高点阻力（{df['trade_date'].iloc[idx].strftime('%Y-%m-%d')}）"
            ))

    # 4. 成交量密集区阻力
    volume_zones = find_volume_support(df)
    for price, vol in volume_zones[:3]:
        if price > current_price:
            resistances.append(PriceLevel(
                price=round(price, 2),
                level_type="成交量密集区",
                strength=4,
                description="成交量密集阻力区"
            ))
            break

    # 去重并排序（按价格升序）
    seen_prices = set()
    unique_resistances = []
    for r in sorted(resistances, key=lambda x: x.price):
        key = round(r.price, 2)
        if key not in seen_prices:
            seen_prices.add(key)
            unique_resistances.append(r)

    return unique_resistances


def generate_buy_suggestions(
    df: pd.DataFrame,
    indicators: Dict,
    supports: List[PriceLevel],
    trend_analysis: Dict
) -> List[BuySuggestion]:
    """
    生成买入建议

    Args:
        df: 原始数据
        indicators: 技术指标字典
        supports: 支撑位列表
        trend_analysis: 趋势分析结果

    Returns:
        买入建议列表
    """
    suggestions = []
    current_price = df['close'].iloc[-1]

    from trend_analyzer import Trend

    # 获取ATR用于动态止损计算
    atr = indicators['atr'].iloc[-1] if not pd.isna(indicators['atr'].iloc[-1]) else current_price * 0.03

    # 获取最近的强支撑位
    nearby_supports = [s for s in supports if s.price < current_price][:3]

    # 根据趋势调整建议
    trend = trend_analysis['trend']

    for support in nearby_supports:
        distance_pct = (current_price - support.price) / current_price * 100

        # 使用ATR计算动态止损（支撑位下方2倍ATR）
        stop_loss_atr = round(support.price - 2 * atr, 2)
        stop_loss_pct = round(support.price * 0.97, 2)
        # 取两者中较高的作为止损
        stop_loss = max(stop_loss_atr, stop_loss_pct)

        # 计算目标价位（支撑位到当前价的1.5-2倍涨幅，考虑ATR）
        risk = current_price - support.price
        target = round(current_price + risk * 1.5, 2)

        # 风险评估（结合KDJ和RSI）
        kdj_j = indicators['kdj']['J'].iloc[-1]
        rsi = indicators['rsi'].iloc[-1]

        if support.strength >= 4 and distance_pct < 10:
            risk_level = "低"
        elif support.strength >= 3:
            risk_level = "中"
        else:
            risk_level = "高"

        # 根据趋势调整建议力度
        if trend == Trend.BULLISH:
            reason = f"趋势向好，{support.level_type}附近可考虑分批建仓"
            risk_adj = risk_level
        elif trend == Trend.BEARISH:
            reason = f"趋势偏弱，{support.level_type}附近可轻仓试探"
            risk_adj = "中" if risk_level == "低" else "高"
        else:  # 震荡
            reason = f"震荡行情，{support.level_type}附近可适度参与"
            risk_adj = risk_level

        suggestions.append(BuySuggestion(
            price=support.price,
            reason=reason,
            risk_level=risk_adj,
            stop_loss=stop_loss,
            target_price=target
        ))

    # 如果KDJ超卖或RSI超卖，增加额外建议
    kdj_j = indicators['kdj']['J'].iloc[-1]
    rsi = indicators['rsi'].iloc[-1]
    wr = indicators['wr'].iloc[-1]

    if rsi < 30 or kdj_j < 0:
        stop_loss = round(current_price - 2 * atr, 2)
        target = round(current_price + 3 * atr, 2)
        reason_parts = []
        if rsi < 30:
            reason_parts.append(f"RSI超卖({rsi:.1f})")
        if kdj_j < 0:
            reason_parts.append(f"KDJ-J超卖({kdj_j:.1f})")
        if wr < -80:
            reason_parts.append(f"WR超卖({wr:.1f})")

        suggestions.append(BuySuggestion(
            price=round(current_price * 0.98, 2),
            reason=f"{', '.join(reason_parts)}，短期反弹概率大",
            risk_level="中",
            stop_loss=stop_loss,
            target_price=target
        ))

    return suggestions


def get_support_resistance_analysis(
    df: pd.DataFrame,
    indicators: Dict,
    trend_analysis: Dict
) -> Dict:
    """
    获取完整的支撑阻力分析

    Args:
        df: 原始数据
        indicators: 技术指标字典
        trend_analysis: 趋势分析结果

    Returns:
        包含支撑位、阻力位和买入建议的字典
    """
    current_price = df['close'].iloc[-1]

    supports = identify_support_levels(df, indicators, current_price)
    resistances = identify_resistance_levels(df, indicators, current_price)
    buy_suggestions = generate_buy_suggestions(df, indicators, supports, trend_analysis)

    return {
        'current_price': current_price,
        'supports': supports,
        'resistances': resistances,
        'buy_suggestions': buy_suggestions,
        'nearest_support': supports[0] if supports else None,
        'nearest_resistance': resistances[0] if resistances else None
    }