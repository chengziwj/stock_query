"""评分器测试"""
import pytest
from stock_scorer import StockScorer, ScoreBreakdown


class TestScoreBreakdown:
    """测试评分数据类"""

    def test_score_creation(self):
        """测试评分对象创建"""
        score = ScoreBreakdown(
            technical=35.0,
            volume_price=25.0,
            trend=15.0,
            risk=8.0,
            total=83.0
        )
        assert score.total == 83.0
        assert score.technical == 35.0


class TestStockScorer:
    """测试股票评分器"""

    def test_init_default_weights(self):
        """测试默认权重"""
        scorer = StockScorer()
        assert scorer.weights['technical'] == 0.40
        assert scorer.weights['volume_price'] == 0.30

    def test_init_custom_weights(self):
        """测试自定义权重"""
        weights = {'technical': 0.5, 'volume_price': 0.3, 'trend': 0.15, 'risk': 0.05}
        scorer = StockScorer(weights=weights)
        assert scorer.weights['technical'] == 0.5
