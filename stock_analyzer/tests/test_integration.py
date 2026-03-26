"""集成测试"""
import pytest

from stock_screener import StockScreener
from stock_scorer import StockScorer
from stock_recommender import StockRecommender
from sector_leaderboard import SectorLeaderboard


class TestIntegration:
    """集成测试"""

    def test_full_recommendation_flow(self):
        """测试完整推荐流程"""
        # 使用小样本测试
        recommender = StockRecommender(top_n=3, max_workers=2)
        result = recommender.recommend_sample(['000001', '600000', '002594'])

        assert result is not None
        assert len(result.stocks) <= 3
        assert result.total_analyzed == 3

    def test_sector_and_scorer_integration(self):
        """测试板块和评分器集成"""
        lb = SectorLeaderboard()
        leaders = lb.get_sector_leaders('银行', top_n=2)

        assert isinstance(leaders, list)
        for leader in leaders:
            assert leader.score is not None
            assert leader.score.total >= 0

    def test_screener_filters(self):
        """测试筛选器"""
        screener = StockScreener(min_market_cap=1000)
        stocks = screener.get_all_stocks()

        # 应该能获取到股票
        assert isinstance(stocks, list)
