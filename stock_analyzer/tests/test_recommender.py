"""推荐器测试"""
import pytest
from stock_recommender import StockRecommender, RecommendationResult


class TestStockRecommender:
    """测试股票推荐器"""

    def test_init(self):
        """测试初始化"""
        recommender = StockRecommender(top_n=20, max_workers=4)
        assert recommender.top_n == 20
        assert recommender.max_workers == 4

    def test_recommend_returns_result(self):
        """测试推荐返回结果"""
        recommender = StockRecommender(top_n=5, max_workers=2)
        # 使用小样本测试
        result = recommender.recommend_sample(['000001', '600000', '002594'])
        assert isinstance(result, RecommendationResult)
        assert len(result.stocks) <= 5
        assert result.total_analyzed == 3
