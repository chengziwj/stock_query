"""价格预测模块 - 基于技术分析的价格预测"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import numpy as np


class PredictionConfidence(Enum):
    """预测置信度"""
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class PricePrediction:
    """价格预测结果"""
    target_price: float
    direction: str  # up / down / sideways
    confidence: PredictionConfidence
    time_frame: str
    probability: float  # 0-100
    reasons: List[str]
    risk_warning: str


def calculate_trend_strength(df: pd.DataFrame, indicators: Dict) -> float:
    """
    计算趋势强度 (0-100)

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        趋势强度分数
    """
    score = 50  # 基准分

    close = df['close'].iloc[-1]

    # MA评分
    ma5 = indicators['ma']['MA5'].iloc[-1]
    ma20 = indicators['ma']['MA20'].iloc[-1]
    ma60 = indicators['ma']['MA60'].iloc[-1]

    if not pd.isna(ma60):
        if close > ma5 > ma20 > ma60:
            score += 20  # 完美多头排列
        elif close < ma5 < ma20 < ma60:
            score -= 20  # 完美空头排列
        elif close > ma20:
            score += 10
        elif close < ma20:
            score -= 10

    # MACD评分
    macd = indicators['macd']['MACD'].iloc[-1]
    dif = indicators['macd']['DIF'].iloc[-1]

    if macd > 0 and dif > 0:
        score += 10
    elif macd < 0 and dif < 0:
        score -= 10

    # RSI评分
    rsi = indicators['rsi'].iloc[-1]
    if 40 <= rsi <= 60:
        pass  # 中性
    elif rsi > 60:
        score += 5
    elif rsi < 40:
        score -= 5

    # KDJ评分
    kdj_k = indicators['kdj']['K'].iloc[-1]
    kdj_d = indicators['kdj']['D'].iloc[-1]

    if kdj_k > kdj_d:
        score += 5
    else:
        score -= 5

    # DMI评分
    plus_di = indicators['dmi']['+DI'].iloc[-1]
    minus_di = indicators['dmi']['-DI'].iloc[-1]
    adx = indicators['dmi']['ADX'].iloc[-1]

    if plus_di > minus_di:
        score += 5
    else:
        score -= 5

    if adx > 25:
        score = score * 1.1  # 趋势明确时放大分数

    return max(0, min(100, score))


def predict_price_range(
    df: pd.DataFrame,
    indicators: Dict,
    sr_analysis: Dict
) -> Dict:
    """
    预测价格区间

    Args:
        df: 原始数据
        indicators: 技术指标字典
        sr_analysis: 支撑阻力分析结果

    Returns:
        价格区间预测
    """
    close = df['close'].iloc[-1]
    atr = indicators['atr'].iloc[-1]

    # 计算趋势强度
    trend_score = calculate_trend_strength(df, indicators)

    # 获取支撑阻力位
    supports = sr_analysis.get('supports', [])
    resistances = sr_analysis.get('resistances', [])

    nearest_support = supports[0].price if supports else close * 0.95
    nearest_resistance = resistances[0].price if resistances else close * 1.05

    # 基于趋势强度的预测
    if trend_score > 65:
        # 看涨
        direction = "up"
        target_short = min(close + 2 * atr, nearest_resistance)
        target_medium = min(close + 4 * atr, nearest_resistance * 1.02)
        target_long = min(close + 6 * atr, nearest_resistance * 1.05)
        probability = min(75, 50 + (trend_score - 50))

    elif trend_score < 35:
        # 看跌
        direction = "down"
        target_short = max(close - 2 * atr, nearest_support)
        target_medium = max(close - 4 * atr, nearest_support * 0.98)
        target_long = max(close - 6 * atr, nearest_support * 0.95)
        probability = min(75, 50 + (50 - trend_score))

    else:
        # 震荡
        direction = "sideways"
        target_short = close + atr * 0.5 * (1 if trend_score > 50 else -1)
        target_medium = close + atr * 0.3 * (1 if trend_score > 50 else -1)
        target_long = close
        probability = 50

    return {
        'direction': direction,
        'trend_score': round(trend_score, 1),
        'targets': {
            'short_term': round(target_short, 2),      # 短期(1-3天)
            'medium_term': round(target_medium, 2),    # 中期(1-2周)
            'long_term': round(target_long, 2),        # 长期(1个月)
        },
        'support_zone': (round(nearest_support * 0.98, 2), round(nearest_support, 2)),
        'resistance_zone': (round(nearest_resistance, 2), round(nearest_resistance * 1.02, 2)),
        'probability': round(probability, 1)
    }


def predict_by_pattern(df: pd.DataFrame, indicators: Dict) -> Dict:
    """
    基于K线形态预测

    Args:
        df: 原始数据
        indicators: 技术指标字典

    Returns:
        形态预测结果
    """
    predictions = []

    close = df['close']
    open_price = df['open']
    high = df['high']
    low = df['low']

    # 最近3根K线
    if len(df) >= 3:
        c1, c2, c3 = close.iloc[-3], close.iloc[-2], close.iloc[-1]
        o1, o2, o3 = open_price.iloc[-3], open_price.iloc[-2], open_price.iloc[-1]
        h1, h2, h3 = high.iloc[-3], high.iloc[-2], high.iloc[-1]
        l1, l2, l3 = low.iloc[-3], low.iloc[-2], low.iloc[-1]

        # 早晨之星（底部反转）
        if o1 > c1 and abs(c2 - o2) < (h1 - l1) * 0.3 and c3 > o3 and c3 > (o1 + c1) / 2:
            predictions.append({
                'pattern': '早晨之星',
                'signal': 'bullish',
                'description': '早晨之星形态，底部反转信号'
            })

        # 黄昏之星（顶部反转）
        if o1 < c1 and abs(c2 - o2) < (h1 - l1) * 0.3 and c3 < o3 and c3 < (o1 + c1) / 2:
            predictions.append({
                'pattern': '黄昏之星',
                'signal': 'bearish',
                'description': '黄昏之星形态，顶部反转信号'
            })

        # 三连阳
        if c3 > c2 > c1 and o3 < c3 and o2 < c2 and o1 < c1:
            predictions.append({
                'pattern': '三连阳',
                'signal': 'bullish',
                'description': '三连阳形态，短期看涨'
            })

        # 三连阴
        if c3 < c2 < c1 and o3 > c3 and o2 > c2 and o1 > c1:
            predictions.append({
                'pattern': '三连阴',
                'signal': 'bearish',
                'description': '三连阴形态，短期看跌'
            })

        # 锤子线（底部）
        body = abs(c3 - o3)
        lower_shadow = min(c3, o3) - l3
        upper_shadow = h3 - max(c3, o3)

        if lower_shadow > body * 2 and upper_shadow < body * 0.5:
            predictions.append({
                'pattern': '锤子线',
                'signal': 'bullish',
                'description': '锤子线形态，可能见底'
            })

        # 流星线（顶部）
        if upper_shadow > body * 2 and lower_shadow < body * 0.5:
            predictions.append({
                'pattern': '流星线',
                'signal': 'bearish',
                'description': '流星线形态，可能见顶'
            })

    return {
        'patterns': predictions,
        'pattern_count': len(predictions)
    }


def generate_prediction(df: pd.DataFrame, indicators: Dict, sr_analysis: Dict, vp_analysis: Dict) -> PricePrediction:
    """
    生成综合价格预测

    Args:
        df: 原始数据
        indicators: 技术指标字典
        sr_analysis: 支撑阻力分析结果
        vp_analysis: 量价分析结果

    Returns:
        价格预测结果
    """
    close = df['close'].iloc[-1]

    # 价格区间预测
    range_pred = predict_price_range(df, indicators, sr_analysis)

    # 形态预测
    pattern_pred = predict_by_pattern(df, indicators)

    # 综合判断
    direction = range_pred['direction']
    trend_score = range_pred['trend_score']
    probability = range_pred['probability']

    # 根据量价关系调整
    vp_signal = vp_analysis.get('signal', 'neutral')
    if vp_signal == 'bullish' and direction == 'up':
        probability = min(85, probability + 10)
    elif vp_signal == 'bearish' and direction == 'down':
        probability = min(85, probability + 10)
    elif vp_signal == 'bullish' and direction == 'down':
        probability = max(40, probability - 10)
    elif vp_signal == 'bearish' and direction == 'up':
        probability = max(40, probability - 10)

    # 根据形态调整
    patterns = pattern_pred.get('patterns', [])
    bullish_patterns = [p for p in patterns if p['signal'] == 'bullish']
    bearish_patterns = [p for p in patterns if p['signal'] == 'bearish']

    if len(bullish_patterns) > len(bearish_patterns) and direction == 'up':
        probability = min(85, probability + 5)
    elif len(bearish_patterns) > len(bullish_patterns) and direction == 'down':
        probability = min(85, probability + 5)

    # 置信度
    if probability >= 70:
        confidence = PredictionConfidence.HIGH
    elif probability >= 55:
        confidence = PredictionConfidence.MEDIUM
    else:
        confidence = PredictionConfidence.LOW

    # 目标价
    target_price = range_pred['targets']['short_term']

    # 时间框架
    if trend_score > 70 or trend_score < 30:
        time_frame = "1-3个交易日"
    elif trend_score > 60 or trend_score < 40:
        time_frame = "1-2周"
    else:
        time_frame = "方向不明"

    # 理由
    reasons = []

    if trend_score > 60:
        reasons.append(f"趋势强度评分{trend_score:.0f}分，偏向看涨")
    elif trend_score < 40:
        reasons.append(f"趋势强度评分{trend_score:.0f}分，偏向看跌")
    else:
        reasons.append(f"趋势强度评分{trend_score:.0f}分，方向不明")

    reasons.append(f"量价关系：{vp_analysis.get('description', '正常')}")

    if bullish_patterns:
        reasons.append(f"发现{len(bullish_patterns)}个看涨形态")
    if bearish_patterns:
        reasons.append(f"发现{len(bearish_patterns)}个看跌形态")

    # 风险提示
    if direction == 'up':
        risk_warning = f"下行风险：跌破{range_pred['support_zone'][0]:.2f}元则预测失效"
    elif direction == 'down':
        risk_warning = f"上行风险：突破{range_pred['resistance_zone'][1]:.2f}元则预测失效"
    else:
        risk_warning = f"关注突破方向：支撑{range_pred['support_zone'][0]:.2f}，阻力{range_pred['resistance_zone'][1]:.2f}"

    return PricePrediction(
        target_price=target_price,
        direction=direction,
        confidence=confidence,
        time_frame=time_frame,
        probability=probability,
        reasons=reasons,
        risk_warning=risk_warning
    )


def get_price_prediction(df: pd.DataFrame, indicators: Dict, sr_analysis: Dict, vp_analysis: Dict) -> Dict:
    """
    获取完整的价格预测

    Args:
        df: 原始数据
        indicators: 技术指标字典
        sr_analysis: 支撑阻力分析结果
        vp_analysis: 量价分析结果

    Returns:
        完整预测结果
    """
    prediction = generate_prediction(df, indicators, sr_analysis, vp_analysis)
    range_pred = predict_price_range(df, indicators, sr_analysis)
    pattern_pred = predict_by_pattern(df, indicators)

    direction_text = {
        'up': '上涨',
        'down': '下跌',
        'sideways': '震荡'
    }

    return {
        'prediction': {
            'direction': direction_text.get(prediction.direction, '震荡'),
            'target_price': prediction.target_price,
            'confidence': prediction.confidence.value,
            'time_frame': prediction.time_frame,
            'probability': prediction.probability,
            'reasons': prediction.reasons,
            'risk_warning': prediction.risk_warning
        },
        'price_range': range_pred,
        'patterns': pattern_pred,
        'support_zone': range_pred['support_zone'],
        'resistance_zone': range_pred['resistance_zone']
    }