"""板块龙头看板模块"""

from typing import Dict, List, Optional
from dataclasses import dataclass

from stock_scorer import StockScorer, ScoreBreakdown


# 预设板块配置
DEFAULT_SECTORS = {
    '银行': ['000001', '600000', '601398', '601939', '601288', '601818'],
    '白酒': ['600519', '000858', '000568', '000596', '600809', '603369'],
    '新能源': ['002594', '300750', '601012', '600438', '300274', '002460'],
    '医药': ['600276', '000538', '600436', '603259', '300760', '600196'],
    '科技': ['688981', '002371', '603501', '300014', '000725', '002230'],
    '消费': ['000333', '000651', '002508', '603288', '600887', '600600'],
    '金融': ['601318', '600030', '601688', '300059', '601211', '600837'],
    '汽车': ['601633', '000625', '600104', '601238', '600660', '603596'],
    '光伏': ['601012', '600438', '002459', '300274', '600732', '603806'],
    '半导体': ['688981', '002371', '603501', '600584', '300782', '603893'],
}


@dataclass
class SectorStock:
    """板块股票"""
    symbol: str
    name: str
    score: ScoreBreakdown
    rank: int


class SectorLeaderboard:
    """
    板块龙头看板

    管理板块配置，提供板块内龙头排序
    """

    def __init__(self, sectors: Optional[Dict[str, List[str]]] = None):
        """
        初始化板块看板

        Args:
            sectors: 自定义板块配置，默认使用预设板块
        """
        self.sectors = sectors or DEFAULT_SECTORS.copy()
        self._scorer = StockScorer()

    def get_sector_leaders(
        self,
        sector_name: str,
        top_n: int = 3
    ) -> List[SectorStock]:
        """
        获取板块内龙头股

        Args:
            sector_name: 板块名称
            top_n: 返回前几名

        Returns:
            排序后的板块股票列表
        """
        if sector_name not in self.sectors:
            return []

        stocks = self.sectors[sector_name]
        results = []

        for symbol in stocks:
            score = self._scorer.score(symbol)
            if score:
                from data_fetcher import StockCodeParser
                name = StockCodeParser.get_stock_name(symbol)
                results.append({
                    'symbol': symbol,
                    'name': name,
                    'score': score,
                    'total': score.total
                })

        # 按总分排序
        results.sort(key=lambda x: x['total'], reverse=True)

        # 构造返回对象
        leaders = []
        for i, r in enumerate(results[:top_n], 1):
            leaders.append(SectorStock(
                symbol=r['symbol'],
                name=r['name'],
                score=r['score'],
                rank=i
            ))

        return leaders

    def get_all_sectors_summary(self, top_n: int = 3) -> Dict[str, List[SectorStock]]:
        """
        获取所有板块概要

        Args:
            top_n: 每个板块返回前几名

        Returns:
            板块到龙头股列表的映射
        """
        summary = {}
        for sector_name in self.sectors:
            summary[sector_name] = self.get_sector_leaders(sector_name, top_n)
        return summary

    def add_sector(self, name: str, stocks: List[str]):
        """
        动态添加板块

        Args:
            name: 板块名称
            stocks: 股票代码列表
        """
        self.sectors[name] = stocks

    def remove_sector(self, name: str):
        """
        删除板块

        Args:
            name: 板块名称
        """
        if name in self.sectors:
            del self.sectors[name]

    def list_sectors(self) -> List[str]:
        """
        列出所有板块名称

        Returns:
            板块名称列表
        """
        return list(self.sectors.keys())
