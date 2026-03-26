"""股票推荐器主模块"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from stock_screener import StockScreener
from stock_scorer import StockScorer, ScoreBreakdown
from data_fetcher import StockCodeParser


@dataclass
class StockRecommendation:
    """股票推荐"""
    symbol: str
    name: str
    score: ScoreBreakdown
    rank: int


@dataclass
class RecommendationResult:
    """推荐结果"""
    date: str
    total_analyzed: int
    stocks: List[StockRecommendation]

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'date': self.date,
            'total_analyzed': self.total_analyzed,
            'stocks': [
                {
                    'rank': s.rank,
                    'symbol': s.symbol,
                    'name': s.name,
                    'score': {
                        'total': s.score.total,
                        'technical': s.score.technical,
                        'volume_price': s.score.volume_price,
                        'trend': s.score.trend,
                        'risk': s.score.risk
                    }
                }
                for s in self.stocks
            ]
        }


class StockRecommender:
    """
    股票推荐器

    整合筛选、分析、评分，生成最终推荐列表
    """

    def __init__(
        self,
        top_n: int = 20,
        max_workers: int = 4,
        min_market_cap: float = 50,
        min_avg_amount: float = 0.5
    ):
        """
        初始化推荐器

        Args:
            top_n: 推荐数量
            max_workers: 并发工作线程数
            min_market_cap: 最小市值（亿）
            min_avg_amount: 最小日均成交额（亿）
        """
        self.top_n = top_n
        self.max_workers = max_workers

        self._screener = StockScreener(
            min_market_cap=min_market_cap,
            min_avg_amount=min_avg_amount
        )
        self._scorer = StockScorer()

    def recommend(self) -> RecommendationResult:
        """
        执行推荐流程

        Returns:
            推荐结果
        """
        from datetime import datetime

        print("正在获取股票列表...")
        # 获取符合条件的股票
        stocks = self._screener.screen()
        total = len(stocks)
        print(f"筛选后剩余 {total} 只股票待分析")

        if total == 0:
            return RecommendationResult(
                date=datetime.now().strftime('%Y-%m-%d'),
                total_analyzed=0,
                stocks=[]
            )

        print(f"开始分析（使用 {self.max_workers} 线程）...")

        # 并发评分
        scored_stocks = self._score_batch(stocks)

        # 排序取Top N
        scored_stocks.sort(key=lambda x: x['score'].total if x['score'] else 0, reverse=True)
        top_stocks = scored_stocks[:self.top_n]

        # 构造推荐结果
        recommendations = []
        for i, item in enumerate(top_stocks, 1):
            if item['score']:
                recommendations.append(StockRecommendation(
                    symbol=item['symbol'],
                    name=item['name'],
                    score=item['score'],
                    rank=i
                ))

        return RecommendationResult(
            date=datetime.now().strftime('%Y-%m-%d'),
            total_analyzed=total,
            stocks=recommendations
        )

    def _score_batch(self, stocks: List[str]) -> List[Dict]:
        """
        批量评分（并发）

        Args:
            stocks: 股票代码列表

        Returns:
            包含评分的股票列表
        """
        results = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(self._score_single, symbol): symbol
                for symbol in stocks
            }

            # 收集结果
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    if completed % 10 == 0:
                        print(f"  已分析 {completed}/{len(stocks)} 只...")
                except Exception as e:
                    print(f"  分析失败 {symbol}: {e}")

        return results

    def _score_single(self, symbol: str) -> Dict:
        """
        单只股票评分

        Args:
            symbol: 股票代码

        Returns:
            评分结果字典
        """
        score = self._scorer.score(symbol)
        name = StockCodeParser.get_stock_name(symbol)

        return {
            'symbol': symbol,
            'name': name,
            'score': score
        }

    def recommend_sample(self, sample_stocks: List[str]) -> RecommendationResult:
        """
        对指定股票样本进行推荐（用于测试）

        Args:
            sample_stocks: 股票代码列表

        Returns:
            推荐结果
        """
        from datetime import datetime

        scored = self._score_batch(sample_stocks)
        scored.sort(key=lambda x: x['score'].total if x['score'] else 0, reverse=True)

        recommendations = []
        for i, item in enumerate(scored[:self.top_n], 1):
            if item['score']:
                recommendations.append(StockRecommendation(
                    symbol=item['symbol'],
                    name=item['name'],
                    score=item['score'],
                    rank=i
                ))

        return RecommendationResult(
            date=datetime.now().strftime('%Y-%m-%d'),
            total_analyzed=len(sample_stocks),
            stocks=recommendations
        )
