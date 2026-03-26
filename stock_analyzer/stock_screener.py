"""股票筛选器模块 - 初步筛选符合条件的股票"""

from typing import List, Dict, Optional
import akshare as ak
import pandas as pd


class StockScreener:
    """
    股票筛选器

    从全市场股票中筛选符合条件的股票
    """

    def __init__(
        self,
        min_market_cap: float = 50,  # 最小市值（亿）
        min_avg_amount: float = 0.5,  # 最小日均成交额（亿）
        exclude_st: bool = True,
        exclude_suspended: bool = True
    ):
        """
        初始化筛选器

        Args:
            min_market_cap: 最小市值（亿人民币）
            min_avg_amount: 最小日均成交额（亿人民币）
            exclude_st: 是否剔除ST股票
            exclude_suspended: 是否剔除停牌股票
        """
        self.min_market_cap = min_market_cap
        self.min_avg_amount = min_avg_amount
        self.exclude_st = exclude_st
        self.exclude_suspended = exclude_suspended

    def get_all_stocks(self) -> List[str]:
        """
        获取全市场A股代码列表

        Returns:
            股票代码列表
        """
        try:
            # 获取实时行情数据
            df = ak.stock_zh_a_spot_em()
            # 提取代码
            codes = df['代码'].tolist()
            return codes
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return []

    def _filter_st_stocks(self, stocks: List[str]) -> List[str]:
        """过滤ST股票"""
        if not self.exclude_st:
            return stocks
        return [s for s in stocks if not s.startswith('ST') and 'ST' not in s]

    def _filter_by_market_cap(
        self,
        stocks: List[str],
        market_data: Optional[pd.DataFrame] = None
    ) -> List[str]:
        """按市值过滤"""
        if market_data is None:
            return stocks

        # 筛选市值大于阈值的股票
        filtered = market_data[
            (market_data['代码'].isin(stocks)) &
            (market_data['总市值'] >= self.min_market_cap * 1e8)
        ]
        return filtered['代码'].tolist()

    def _filter_by_amount(
        self,
        stocks: List[str],
        market_data: Optional[pd.DataFrame] = None
    ) -> List[str]:
        """按成交额过滤"""
        if market_data is None:
            return stocks

        filtered = market_data[
            (market_data['代码'].isin(stocks)) &
            (market_data['成交额'] >= self.min_avg_amount * 1e8)
        ]
        return filtered['代码'].tolist()

    def screen(self) -> List[str]:
        """
        执行完整筛选流程

        Returns:
            符合条件的股票代码列表
        """
        # 获取全市场股票
        all_stocks = self.get_all_stocks()
        if not all_stocks:
            return []

        # 获取市场数据
        try:
            market_data = ak.stock_zh_a_spot_em()
        except:
            market_data = None

        # 应用过滤条件
        filtered = all_stocks

        if self.exclude_st:
            filtered = self._filter_st_stocks(filtered)

        if market_data is not None:
            filtered = self._filter_by_market_cap(filtered, market_data)
            filtered = self._filter_by_amount(filtered, market_data)

        return filtered
