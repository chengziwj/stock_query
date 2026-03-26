"""股票评分器模块 - 综合评分系统"""

from typing import Dict, Optional
from dataclasses import dataclass

import pandas as pd
import numpy as np

from data_processor import DataProcessor


@dataclass
class ScoreBreakdown:
    """评分明细"""
    technical: float      # 技术指标得分 (0-40)
    volume_price: float   # 量价关系得分 (0-30)
    trend: float          # 趋势预测得分 (0-20)
    risk: float           # 风险控制得分 (0-10)
    total: float          # 总分 (0-100)

    def __str__(self):
        return f"总分:{self.total:.1f} 技术:{self.technical:.1f} 量价:{self.volume_price:.1f} 趋势:{self.trend:.1f} 风控:{self.risk:.1f}"


class StockScorer:
    """
    股票评分器

    对单只股票进行多维度综合评分
    """

    # 默认权重
    DEFAULT_WEIGHTS = {
        'technical': 0.40,    # 技术指标
        'volume_price': 0.30, # 量价关系
        'trend': 0.20,        # 趋势预测
        'risk': 0.10          # 风险控制
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化评分器

        Args:
            weights: 自定义权重，默认使用平衡配置
        """
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._processor = DataProcessor()

    def score(self, symbol: str) -> Optional[ScoreBreakdown]:
        """
        对单只股票进行评分

        Args:
            symbol: 股票代码

        Returns:
            评分明细，失败返回None
        """
        try:
            # 获取完整分析
            result = self._processor.analyze(symbol)

            # 计算各维度得分
            technical = self._calc_technical_score(result)
            volume_price = self._calc_volume_price_score(result)
            trend = self._calc_trend_score(result)
            risk = self._calc_risk_score(result)

            # 计算总分
            total = (
                technical * self.weights['technical'] +
                volume_price * self.weights['volume_price'] +
                trend * self.weights['trend'] +
                risk * self.weights['risk']
            ) / sum(self.weights.values()) * 100 / 40  # 归一化到100分制

            return ScoreBreakdown(
                technical=technical,
                volume_price=volume_price,
                trend=trend,
                risk=risk,
                total=min(100, max(0, total))
            )

        except Exception as e:
            print(f"评分失败 {symbol}: {e}")
            return None

    def _calc_technical_score(self, result: Dict) -> float:
        """计算技术指标得分 (0-40)"""
        score = 0.0
        indicators = result['indicators']
        latest = result['latest']

        # MA排列得分 (10分)
        ma5 = latest['ma']['MA5']
        ma10 = latest['ma']['MA10']
        ma20 = latest['ma']['MA20']
        ma60 = latest['ma']['MA60']

        if ma60 and ma5 > ma10 > ma20 > ma60:
            score += 10  # 完美多头排列
        elif ma60 and ma5 > ma20 > ma60:
            score += 7
        elif ma5 > ma20:
            score += 4
        elif ma5 < ma20:
            score += 2
        else:
            score += 3

        # MACD得分 (10分)
        macd = latest['macd']['MACD']
        dif = latest['macd']['DIF']
        dea = latest['macd']['DEA']

        if macd > 0 and dif > 0 and dea > 0:
            score += 10  # 零轴上金叉或多头排列
        elif macd > 0:
            score += 6   # 零轴下金叉
        elif dif > dea:
            score += 4   # 多头排列
        else:
            score += 1   # 死叉

        # KDJ得分 (10分)
        k = latest['kdj']['K']
        d = latest['kdj']['D']

        if 20 < k < 80 and k > d:
            score += 10  # 健康金叉
        elif k < 20 and k > d:
            score += 8   # 超卖区金叉
        elif k > 80 and k < d:
            score += 2   # 超买区死叉
        elif k < d:
            score += 3   # 死叉
        else:
            score += 5

        # RSI得分 (10分)
        rsi = latest['rsi']
        if 40 <= rsi <= 60:
            score += 5   # 中性区
        elif 60 < rsi < 70:
            score += 7   # 强势区
        elif rsi >= 70:
            score += 9   # 超买区（但可能继续涨）
        elif 30 < rsi < 40:
            score += 3   # 弱势区
        else:
            score += 1   # 超卖区（可能反弹）

        return score

    def _calc_volume_price_score(self, result: Dict) -> float:
        """计算量价关系得分 (0-30)"""
        score = 0.0
        vp = result['volume_price']

        # 量价形态得分 (15分)
        pattern = vp['pattern']
        strength = vp['strength']

        if pattern == '价升量增':
            score += 15
        elif pattern == '放量突破':
            score += 13
        elif pattern == '价跌量缩':
            score += 10
        elif pattern == '缩量盘整':
            score += 5
        elif pattern == '价升量缩':
            score += 3
        else:
            score += strength * 2  # 其他形态按强度

        # 资金流向得分 (10分)
        money_flow = vp['money_flow']
        flow_signal = money_flow['flow_signal']

        if flow_signal == 'bullish' and money_flow['net_inflow_pct'] > 20:
            score += 10  # 大幅流入
        elif flow_signal == 'bullish':
            score += 7   # 小幅流入
        elif flow_signal == 'neutral':
            score += 5   # 平衡
        else:
            score += 2   # 流出

        # 极端成交量得分 (5分)
        extreme = vp.get('extreme_volume', {})
        if extreme.get('detected'):
            if extreme.get('signal') == 'bullish':
                score += 5   # 地量见地价
            else:
                score += 0   # 天量见天价（扣分）
        else:
            score += 3   # 正常

        return score

    def _calc_trend_score(self, result: Dict) -> float:
        """计算趋势预测得分 (0-20)"""
        score = 0.0

        # 趋势判断得分 (10分)
        analysis = result['analysis']
        trend = analysis['trend']

        if trend == 1:  # 看涨
            score += 10
        elif trend == 0:  # 震荡
            score += 5
        else:  # 看跌
            score += 0

        # 预测置信度得分 (10分)
        prediction = result['prediction']
        confidence = prediction['prediction']['confidence']

        if confidence == '高':
            score += 10
        elif confidence == '中':
            score += 6
        else:
            score += 3

        return score

    def _calc_risk_score(self, result: Dict) -> float:
        """计算风险控制得分 (0-10)"""
        score = 0.0
        indicators = result['indicators']
        latest = result['latest']

        # 波动率得分 (5分)
        atr = latest['atr']
        close = result['data']['close'].iloc[-1]
        atr_ratio = atr / close if close > 0 else 0

        if 0.01 < atr_ratio < 0.03:  # 适中波动
            score += 5
        elif atr_ratio < 0.01:  # 过低波动
            score += 3
        else:  # 过高波动
            score += 2

        # 位置风险得分 (5分)
        price_position = result['features']['features']['price_position']

        if 0.3 < price_position < 0.7:  # 价格居中
            score += 5
        elif price_position < 0.3:  # 接近支撑
            score += 4
        else:  # 接近阻力
            score += 2

        return score
