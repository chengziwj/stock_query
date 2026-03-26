"""趋势分析模块 - 综合技术指标分析股票趋势"""

from enum import Enum
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


class Trend(Enum):
    """趋势类型"""

    BULLISH = "看涨"
    BEARISH = "看跌"
    OSCILLATING = "震荡"


class Signal(Enum):
    """信号类型"""

    BULLISH = 1  # 看涨
    BEARISH = -1  # 看跌
    NEUTRAL = 0  # 中性


def analyze_ma_signal(df: pd.DataFrame, indicators: Dict) -> Tuple[Signal, List[str]]:
    """
    分析均线信号

    看涨：价格 > MA5 > MA20 > MA60
    看跌：价格 < MA5 < MA20 < MA60

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        (信号类型, 理由列表)
    """
    signals = []
    reasons = []

    close = df["close"].iloc[-1]
    ma5 = indicators["ma"]["MA5"].iloc[-1]
    ma20 = indicators["ma"]["MA20"].iloc[-1]
    ma60 = indicators["ma"]["MA60"].iloc[-1]

    # 检查MA60是否有效
    ma60_valid = not pd.isna(ma60)

    # 价格与MA5关系
    if close > ma5:
        signals.append(Signal.BULLISH)
        reasons.append("价格位于MA5上方，短期趋势向上")
    elif close < ma5:
        signals.append(Signal.BEARISH)
        reasons.append("价格位于MA5下方，短期趋势向下")

    # MA5与MA20关系
    if ma5 > ma20:
        signals.append(Signal.BULLISH)
        reasons.append("MA5上穿MA20，短期均线金叉")
    elif ma5 < ma20:
        signals.append(Signal.BEARISH)
        reasons.append("MA5下穿MA20，短期均线死叉")

    # MA20与MA60关系
    if ma60_valid:
        if ma20 > ma60:
            signals.append(Signal.BULLISH)
            reasons.append("MA20位于MA60上方，中期趋势向好")
        elif ma20 < ma60:
            signals.append(Signal.BEARISH)
            reasons.append("MA20位于MA60下方，中期趋势偏弱")

    # 完美多头/空头排列
    if ma60_valid:
        if close > ma5 > ma20 > ma60:
            signals.append(Signal.BULLISH)
            reasons.append("均线呈完美多头排列")
        elif close < ma5 < ma20 < ma60:
            signals.append(Signal.BEARISH)
            reasons.append("均线呈完美空头排列")

    # 综合信号
    bullish_count = sum(1 for s in signals if s == Signal.BULLISH)
    bearish_count = sum(1 for s in signals if s == Signal.BEARISH)

    if bullish_count > bearish_count:
        return Signal.BULLISH, reasons
    elif bearish_count > bullish_count:
        return Signal.BEARISH, reasons
    else:
        return Signal.NEUTRAL, ["均线信号不明确"]


def analyze_rsi_signal(indicators: Dict) -> Tuple[Signal, List[str]]:
    """
    分析RSI信号

    超买：RSI > 70
    超卖：RSI < 30
    中性：RSI在50附近

    Args:
        indicators: 技术指标字典

    Returns:
        (信号类型, 理由列表)
    """
    reasons = []
    rsi = indicators["rsi"].iloc[-1]

    if pd.isna(rsi):
        return Signal.NEUTRAL, ["RSI数据不足"]

    if rsi > 80:
        return Signal.BEARISH, [f"RSI({rsi:.1f})严重超买，短期回调风险较大"]
    elif rsi > 70:
        return Signal.BEARISH, [f"RSI({rsi:.1f})超买区域，注意回调风险"]
    elif rsi < 20:
        return Signal.BULLISH, [f"RSI({rsi:.1f})严重超卖，短期反弹概率较大"]
    elif rsi < 30:
        return Signal.BULLISH, [f"RSI({rsi:.1f})超卖区域，可能存在反弹机会"]
    elif rsi > 50:
        return Signal.BULLISH, [f"RSI({rsi:.1f})位于强势区域，买方力量占优"]
    elif rsi < 50:
        return Signal.BEARISH, [f"RSI({rsi:.1f})位于弱势区域，卖方力量占优"]
    else:
        return Signal.NEUTRAL, [f"RSI({rsi:.1f})位于中性区域"]


def analyze_macd_signal(indicators: Dict) -> Tuple[Signal, List[str]]:
    """
    分析MACD信号

    金叉：DIF上穿DEA（看涨）
    死叉：DIF下穿DEA（看跌）

    Args:
        indicators: 技术指标字典

    Returns:
        (信号类型, 理由列表)
    """
    reasons = []

    dif = indicators["macd"]["DIF"]
    dea = indicators["macd"]["DEA"]
    macd = indicators["macd"]["MACD"]

    last_dif = dif.iloc[-1]
    last_dea = dea.iloc[-1]
    last_macd = macd.iloc[-1]

    # 检查前一天的值（如果有足够数据）
    if len(dif) >= 2:
        prev_dif = dif.iloc[-2]
        prev_dea = dea.iloc[-2]

        # 金叉检测
        if prev_dif <= prev_dea and last_dif > last_dea:
            if last_dif < 0:
                reasons.append("MACD零轴下方金叉，可能迎来反弹")
            else:
                reasons.append("MACD零轴上方金叉，上涨动能增强")
            return Signal.BULLISH, reasons

        # 死叉检测
        if prev_dif >= prev_dea and last_dif < last_dea:
            if last_dif > 0:
                reasons.append("MACD零轴上方死叉，注意回调风险")
            else:
                reasons.append("MACD零轴下方死叉，下跌动能增强")
            return Signal.BEARISH, reasons

    # DIF与DEA位置关系
    if last_dif > last_dea:
        if last_dif > 0:
            reasons.append("MACD多头排列，DIF在零轴上方")
            return Signal.BULLISH, reasons
        else:
            reasons.append("MACD零轴下方多头排列")
            return Signal.BULLISH, reasons
    elif last_dif < last_dea:
        if last_dif < 0:
            reasons.append("MACD空头排列，DIF在零轴下方")
            return Signal.BEARISH, reasons
        else:
            reasons.append("MACD零轴上方空头排列")
            return Signal.BEARISH, reasons

    return Signal.NEUTRAL, ["MACD信号不明确"]


def analyze_bollinger_signal(
    df: pd.DataFrame, indicators: Dict
) -> Tuple[Signal, List[str]]:
    """
    分析布林带信号

    上轨突破：价格 > 上轨（可能超买）
    下轨突破：价格 < 下轨（可能超卖）
    通道内运行：趋势延续

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        (信号类型, 理由列表)
    """
    reasons = []

    close = df["close"].iloc[-1]
    upper = indicators["bollinger"]["upper"].iloc[-1]
    middle = indicators["bollinger"]["middle"].iloc[-1]
    lower = indicators["bollinger"]["lower"].iloc[-1]

    if pd.isna(upper) or pd.isna(middle) or pd.isna(lower):
        return Signal.NEUTRAL, ["布林带数据不足"]

    # 计算价格在布林带中的位置
    band_width = upper - lower
    position = (close - lower) / band_width if band_width > 0 else 0.5

    if close > upper:
        reasons.append(f"价格突破布林带上轨({upper:.2f})，强势特征明显，但注意超买风险")
        return Signal.BULLISH, reasons
    elif close < lower:
        reasons.append(f"价格跌破布林带下轨({lower:.2f})，弱势明显，但存在超卖反弹可能")
        return Signal.BULLISH, reasons  # 超卖可能反弹
    elif close > middle:
        if position > 0.75:
            reasons.append("价格运行在布林带中上轨区域，显示强势")
        else:
            reasons.append("价格位于布林带中轨上方")
        return Signal.BULLISH, reasons
    else:
        if position < 0.25:
            reasons.append("价格运行在布林带中下轨区域，显示弱势")
        else:
            reasons.append("价格位于布林带中轨下方")
        return Signal.BEARISH, reasons


def analyze_trend(df: pd.DataFrame, indicators: Dict) -> Tuple[Trend, List[str]]:
    """
    综合趋势分析

    判断规则：
    - 看涨：至少3个指标支持看涨，且无强烈看跌信号
    - 看跌：至少3个指标支持看跌，且无强烈看涨信号
    - 震荡：指标矛盾或无明显趋势信号

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        (趋势类型, 判断理由列表)
    """
    all_reasons = []

    # 各指标分析
    ma_signal, ma_reasons = analyze_ma_signal(df, indicators)
    all_reasons.extend(ma_reasons)

    rsi_signal, rsi_reasons = analyze_rsi_signal(indicators)
    all_reasons.extend(rsi_reasons)

    macd_signal, macd_reasons = analyze_macd_signal(indicators)
    all_reasons.extend(macd_reasons)

    bollinger_signal, bollinger_reasons = analyze_bollinger_signal(df, indicators)
    all_reasons.extend(bollinger_reasons)

    # 统计信号
    signals = [ma_signal, rsi_signal, macd_signal, bollinger_signal]
    bullish_count = sum(1 for s in signals if s == Signal.BULLISH)
    bearish_count = sum(1 for s in signals if s == Signal.BEARISH)

    # 综合判断
    if bullish_count >= 3 and bearish_count < 2:
        return Trend.BULLISH, all_reasons
    elif bearish_count >= 3 and bullish_count < 2:
        return Trend.BEARISH, all_reasons
    else:
        return Trend.OSCILLATING, all_reasons


def get_trend_analysis(df: pd.DataFrame, indicators: Dict) -> Dict:
    """
    获取完整的趋势分析结果

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        包含趋势判断和理由的字典
    """
    trend, reasons = analyze_trend(df, indicators)

    return {
        "trend": trend,
        "trend_text": trend.value,
        "reasons": reasons,
        "signals": {
            "ma": analyze_ma_signal(df, indicators)[0].value,
            "rsi": analyze_rsi_signal(indicators)[0].value,
            "macd": analyze_macd_signal(indicators)[0].value,
            "bollinger": analyze_bollinger_signal(df, indicators)[0].value,
        },
    }
