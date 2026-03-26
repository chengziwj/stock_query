"""板块龙头看板测试"""
import pytest
from sector_leaderboard import SectorLeaderboard, SectorStock


class TestSectorLeaderboard:
    """测试板块看板"""

    def test_init_default_sectors(self):
        """测试默认板块"""
        lb = SectorLeaderboard()
        assert '银行' in lb.sectors
        assert '白酒' in lb.sectors

    def test_init_custom_sectors(self):
        """测试自定义板块"""
        custom = {'测试板块': ['000001', '600000']}
        lb = SectorLeaderboard(sectors=custom)
        assert '测试板块' in lb.sectors

    def test_get_sector_leaders(self):
        """测试获取板块龙头"""
        lb = SectorLeaderboard()
        leaders = lb.get_sector_leaders('银行', top_n=3)
        assert isinstance(leaders, list)
        assert len(leaders) <= 3
