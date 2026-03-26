# A股股票推荐系统实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 构建基于技术信号的股票推荐系统，从全市场筛选Top 20，并提供板块龙头看板。

**Architecture:** 采用分层架构：筛选层→分析层→评分层→输出层。复用现有技术分析能力，通过并发处理优化性能。

**Tech Stack:** Python, akshare, pandas, concurrent.futures, pytest

---

## 实施阶段

### Phase 1: 基础模块 - StockScreener（筛选器）

#### Task 1: 创建筛选器测试文件

**Files:**
- Create: `stock_analyzer/tests/test_screener.py`

**Step 1: 编写基础测试**

```python
"""筛选器测试"""
import pytest
from stock_screener import StockScreener


class TestStockScreener:
    """测试股票筛选器"""

    def test_init(self):
        """测试初始化"""
        screener = StockScreener()
        assert screener is not None

    def test_filter_st_stocks(self):
        """测试ST股票过滤"""
        screener = StockScreener()
        stocks = ['000001', '000002', 'ST0001', '600000']
        filtered = screener._filter_st_stocks(stocks)
        assert 'ST0001' not in filtered
        assert len(filtered) == 3

    def test_filter_by_market_cap(self):
        """测试市值过滤"""
        screener = StockScreener(min_market_cap=50)
        # 模拟市值数据
        result = screener._filter_by_market_cap(['000001', '000002'])
        assert isinstance(result, list)
```

**Step 2: 运行测试确认失败**

```bash
cd D:/py/stock/stock_analyzer
.venv\Scripts\python -m pytest tests/test_screener.py -v
```

Expected: `ModuleNotFoundError: No module named 'stock_screener'`

**Step 3: 创建筛选器实现**

Create: `stock_analyzer/stock_screener.py`

```python
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
```

**Step 4: 运行测试确认通过**

```bash
.venv\Scripts\python -m pytest tests/test_screener.py -v
```

Expected: 3 passed

**Step 5: 提交**

```bash
cd D:/py/stock
git add stock_analyzer/stock_screener.py stock_analyzer/tests/test_screener.py
git commit -m "feat: add StockScreener module for stock filtering"
```

---

### Phase 2: 核心模块 - StockScorer（评分器）

#### Task 2: 创建评分器测试

**Files:**
- Create: `stock_analyzer/tests/test_scorer.py`

**Step 1: 编写测试**

```python
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

    def test_score_ma_alignment(self):
        """测试MA排列评分"""
        scorer = StockScorer()
        # 多头排列
        score = scorer._score_ma_alignment(1.5)  # MA得分
        assert score > 7
        # 空头排列
        score = scorer._score_ma_alignment(-1.5)
        assert score < 3
```

**Step 2: 运行测试确认失败**

```bash
.venv\Scripts\python -m pytest tests/test_scorer.py -v
```

Expected: `ModuleNotFoundError`

**Step 3: 创建评分器实现**

Create: `stock_analyzer/stock_scorer.py`

```python
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
```

**Step 4: 运行测试确认通过**

```bash
.venv\Scripts\python -m pytest tests/test_scorer.py -v
```

Expected: All passed

**Step 5: 提交**

```bash
git add stock_analyzer/stock_scorer.py stock_analyzer/tests/test_scorer.py
git commit -m "feat: add StockScorer with comprehensive scoring system"
```

---

### Phase 3: 板块模块 - SectorLeaderboard

#### Task 3: 创建板块看板测试和实现

**Files:**
- Create: `stock_analyzer/tests/test_sector_leaderboard.py`
- Create: `stock_analyzer/sector_leaderboard.py`

**Step 1: 编写测试**

```python
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
```

**Step 2: 运行测试确认失败**

**Step 3: 创建实现**

Create: `stock_analyzer/sector_leaderboard.py`

```python
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
```

**Step 4: 运行测试确认通过**

```bash
.venv\Scripts\python -m pytest tests/test_sector_leaderboard.py -v
```

**Step 5: 提交**

```bash
git add stock_analyzer/sector_leaderboard.py stock_analyzer/tests/test_sector_leaderboard.py
git commit -m "feat: add SectorLeaderboard for sector-based stock ranking"
```

---

### Phase 4: 推荐器主模块 - StockRecommender

#### Task 4: 创建推荐器测试和实现

**Files:**
- Create: `stock_analyzer/tests/test_recommender.py`
- Create: `stock_analyzer/stock_recommender.py`

**Step 1: 编写测试**

```python
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
        result = recommender.recommend_sample(['000001', '600000'])
        assert isinstance(result, RecommendationResult)
        assert len(result.stocks) <= 5
```

**Step 2: 运行测试确认失败**

**Step 3: 创建实现**

Create: `stock_analyzer/stock_recommender.py`

```python
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
```

**Step 4: 运行测试确认通过**

```bash
.venv\Scripts\python -m pytest tests/test_recommender.py -v
```

**Step 5: 提交**

```bash
git add stock_analyzer/stock_recommender.py stock_analyzer/tests/test_recommender.py
git commit -m "feat: add StockRecommender with concurrent scoring"
```

---

### Phase 5: 报告格式化模块

#### Task 5: 创建报告模块

**Files:**
- Create: `stock_analyzer/recommendation_report.py`

**实现**:

```python
"""推荐报告格式化模块"""

from typing import List
import csv

from stock_recommender import RecommendationResult, StockRecommendation
from console_ui import Colors, colorize, draw_box, draw_section


class RecommendationReporter:
    """推荐报告格式化器"""

    @staticmethod
    def format_console(result: RecommendationResult) -> str:
        """格式化命令行输出"""
        lines = []

        # 标题
        lines.append(colorize(f"╔══════════════════════════════════════════════════════════════════╗", Colors.BRIGHT_CYAN))
        lines.append(colorize(f"║", Colors.BRIGHT_CYAN) + colorize(f"              A股股票推荐榜 ({result.date})                           ", Colors.BRIGHT_YELLOW + Colors.BOLD) + colorize(f"║", Colors.BRIGHT_CYAN))
        lines.append(colorize(f"║", Colors.BRIGHT_CYAN) + f"              综合评分排序 | 共分析 {result.total_analyzed} 只             " + colorize(f"║", Colors.BRIGHT_CYAN))
        lines.append(colorize(f"╠════╦══════════╦════════╦════════╦══════════╦══════════╦═════════╣", Colors.BRIGHT_CYAN))
        lines.append(colorize(f"║", Colors.BRIGHT_CYAN) + colorize("排名", Colors.BRIGHT_YELLOW) + colorize(f"║", Colors.BRIGHT_CYAN) + " 股票代码 " + colorize(f"║", Colors.BRIGHT_CYAN) + " 股票名 " + colorize(f"║", Colors.BRIGHT_CYAN) + colorize("总分  ", Colors.BRIGHT_YELLOW) + colorize(f"║", Colors.BRIGHT_CYAN) + " 技术面   " + colorize(f"║", Colors.BRIGHT_CYAN) + " 资金面   " + colorize(f"║", Colors.BRIGHT_CYAN) + " 趋势    " + colorize(f"║", Colors.BRIGHT_CYAN))
        lines.append(colorize(f"╠════╬══════════╬════════╬════════╬══════════╬══════════╬═════════╣", Colors.BRIGHT_CYAN))

        # 股票列表
        for stock in result.stocks:
            score = stock.score
            trend = "看涨" if score.trend >= 15 else "震荡" if score.trend >= 8 else "看跌"
            trend_color = Colors.BRIGHT_RED if trend == "看涨" else Colors.BRIGHT_YELLOW if trend == "震荡" else Colors.BRIGHT_GREEN

            lines.append(
                f"{colorize('║', Colors.BRIGHT_CYAN)}  {stock.rank:>2} "
                f"{colorize('║', Colors.BRIGHT_CYAN)} {stock.symbol:<8} "
                f"{colorize('║', Colors.BRIGHT_CYAN)} {stock.name:<6} "
                f"{colorize('║', Colors.BRIGHT_CYAN)} {colorize(f'{score.total:>5.1f}', Colors.BRIGHT_CYAN + Colors.BOLD)} "
                f"{colorize('║', Colors.BRIGHT_CYAN)} {RecommendationReporter._stars(score.technical/40*5)} "
                f"{colorize('║', Colors.BRIGHT_CYAN)} {RecommendationReporter._stars(score.volume_price/30*5)} "
                f"{colorize('║', Colors.BRIGHT_CYAN)} {colorize(trend, trend_color):<7} "
                f"{colorize('║', Colors.BRIGHT_CYAN)}"
            )

        lines.append(colorize(f"╚════╩══════════╩════════╩════════╩══════════╩══════════╩═════════╝", Colors.BRIGHT_CYAN))
        lines.append("")
        lines.append(colorize("[1] 查看详细分析  [2] 导出CSV  [3] 查看板块龙头  [q] 退出", Colors.DIM))

        return '\n'.join(lines)

    @staticmethod
    def _stars(rating: float) -> str:
        """生成星级显示"""
        filled = int(rating)
        empty = 5 - filled
        return '★' * filled + '☆' * empty

    @staticmethod
    def export_csv(result: RecommendationResult, filepath: str):
        """导出CSV"""
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['排名', '股票代码', '股票名称', '总分', '技术面', '量价', '趋势', '风控'])

            for stock in result.stocks:
                s = stock.score
                writer.writerow([
                    stock.rank,
                    stock.symbol,
                    stock.name,
                    f"{s.total:.1f}",
                    f"{s.technical:.1f}",
                    f"{s.volume_price:.1f}",
                    f"{s.trend:.1f}",
                    f"{s.risk:.1f}"
                ])

        print(f"已导出到: {filepath}")
```

**提交**:

```bash
git add stock_analyzer/recommendation_report.py
git commit -m "feat: add RecommendationReporter for formatting output"
```

---

### Phase 6: 命令行界面

#### Task 6: 创建CLI

**Files:**
- Create: `stock_analyzer/recommendation_cli.py`

**实现**:

```python
"""推荐系统命令行界面"""

import sys
import io
from typing import Optional

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from stock_recommender import StockRecommender
from sector_leaderboard import SectorLeaderboard
from recommendation_report import RecommendationReporter
from console_ui import print_welcome, print_goodbye, Colors, colorize


def print_menu():
    """打印菜单"""
    print()
    print(colorize("  ╔══════════════════════════════════════════════════════╗", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "          " + colorize("A股股票推荐系统", Colors.BRIGHT_YELLOW + Colors.BOLD) + "                           " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ╠══════════════════════════════════════════════════════╣", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "  [1] 生成股票推荐榜 (Top 20)                          " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "  [2] 查看板块龙头看板                                 " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "  [3] 导出推荐结果到CSV                                " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "  [q] 退出                                             " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ╚══════════════════════════════════════════════════════╝", Colors.BRIGHT_CYAN))
    print()


def run_recommendation():
    """运行推荐"""
    print()
    print(colorize("正在初始化推荐系统...", Colors.CYAN))

    recommender = StockRecommender(top_n=20, max_workers=4)

    print(colorize("开始分析全市场股票，请稍候...", Colors.CYAN))
    print(colorize("(预计需要 5-10 分钟)", Colors.DIM))
    print()

    result = recommender.recommend()

    # 显示结果
    output = RecommendationReporter.format_console(result)
    print(output)

    return result


def show_sector_leaderboard():
    """显示板块龙头看板"""
    lb = SectorLeaderboard()

    print()
    print(colorize("╔════════════════════════════════════════════════════════════╗", Colors.BRIGHT_CYAN))
    print(colorize("║", Colors.BRIGHT_CYAN) + colorize("                   板块龙头看板                              ", Colors.BRIGHT_YELLOW + Colors.BOLD) + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("╠════════════╦═══════════════════════════════════════════════╣", Colors.BRIGHT_CYAN))
    print(colorize("║", Colors.BRIGHT_CYAN) + " 板块       " + colorize("║", Colors.BRIGHT_CYAN) + " 龙头股 (按强度排序)                            " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("╠════════════╬═══════════════════════════════════════════════╣", Colors.BRIGHT_CYAN))

    for sector_name in lb.list_sectors():
        leaders = lb.get_sector_leaders(sector_name, top_n=3)
        leader_str = " ".join([f"{s.name}({s.score.total:.1f})" for s in leaders[:3]])
        print(colorize("║", Colors.BRIGHT_CYAN) + f" {sector_name:<10} " + colorize("║", Colors.BRIGHT_CYAN) + f" {leader_str:<45} " + colorize("║", Colors.BRIGHT_CYAN))

    print(colorize("╚════════════╩═══════════════════════════════════════════════╝", Colors.BRIGHT_CYAN))
    print()

    # 允许查看详细
    sector_input = input(colorize("请输入板块名称查看详细 (直接回车返回): ", Colors.CYAN)).strip()
    if sector_input:
        show_sector_detail(sector_input)


def show_sector_detail(sector_name: str):
    """显示板块详情"""
    lb = SectorLeaderboard()

    if sector_name not in lb.sectors:
        print(colorize(f"未知板块: {sector_name}", Colors.BRIGHT_RED))
        return

    leaders = lb.get_sector_leaders(sector_name, top_n=6)

    print()
    print(colorize(f"═══ {sector_name} 板块龙头股 ═══", Colors.BRIGHT_YELLOW + Colors.BOLD))
    print()

    for s in leaders:
        score = s.score
        print(f"  {s.rank}. {s.symbol} {s.name}")
        print(f"     总分: {colorize(f'{score.total:.1f}', Colors.BRIGHT_CYAN)} | "
              f"技术: {score.technical:.1f} | "
              f"量价: {score.volume_price:.1f} | "
              f"趋势: {score.trend:.1f}")
        print()


def export_result(result, filepath: str = "recommendation.csv"):
    """导出结果"""
    if result is None:
        print(colorize("请先运行推荐", Colors.BRIGHT_RED))
        return

    RecommendationReporter.export_csv(result, filepath)


def main():
    """主函数"""
    print_welcome()
    print_menu()

    current_result = None

    while True:
        choice = input(colorize("  > ", Colors.BRIGHT_CYAN)).strip().lower()

        if choice == 'q':
            print_goodbye()
            break

        elif choice == '1':
            current_result = run_recommendation()

        elif choice == '2':
            show_sector_leaderboard()

        elif choice == '3':
            if current_result:
                filepath = input("  导出文件名 (默认: recommendation.csv): ").strip() or "recommendation.csv"
                export_result(current_result, filepath)
            else:
                print(colorize("  请先运行推荐 (选项1)", Colors.BRIGHT_YELLOW))

        elif choice == 'menu':
            print_menu()

        elif choice == '':
            continue

        else:
            print(colorize("  无效选项，请重新选择", Colors.BRIGHT_RED))


if __name__ == "__main__":
    main()
```

**提交**:

```bash
git add stock_analyzer/recommendation_cli.py
git commit -m "feat: add recommendation CLI with interactive menu"
```

---

### Phase 7: 集成测试

#### Task 7: 创建集成测试

**Files:**
- Create: `stock_analyzer/tests/test_integration.py`

**测试内容**:

```python
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
```

**运行测试**:

```bash
.venv\Scripts\python -m pytest tests/test_integration.py -v
```

**提交**:

```bash
git add stock_analyzer/tests/test_integration.py
git commit -m "test: add integration tests"
```

---

### Phase 8: 最终验证

#### Task 8: 运行全部测试

```bash
.venv\Scripts\python -m pytest tests/ -v --tb=short
```

Expected: All tests pass

#### Task 9: 功能验证

```bash
# 测试CLI菜单显示
.venv\Scripts\python recommendation_cli.py
# 输入: menu, 然后 q 退出

# 测试板块看板
.venv\Scripts\python -c "from recommendation_cli import show_sector_leaderboard; show_sector_leaderboard()"
```

#### Task 10: 最终提交

```bash
git add -A
git commit -m "feat: complete stock recommendation system with sector leaderboard

- Add StockScreener for filtering stocks
- Add StockScorer with comprehensive scoring (technical/volume/trend/risk)
- Add SectorLeaderboard for sector-based ranking
- Add StockRecommender with concurrent processing
- Add CLI with interactive menu
- Add tests for all modules"
```

---

## 总结

**新增文件**:
- `stock_screener.py` - 筛选器
- `stock_scorer.py` - 评分器
- `sector_leaderboard.py` - 板块看板
- `stock_recommender.py` - 推荐器
- `recommendation_report.py` - 报告格式化
- `recommendation_cli.py` - 命令行界面
- `tests/test_screener.py` - 筛选器测试
- `tests/test_scorer.py` - 评分器测试
- `tests/test_sector_leaderboard.py` - 板块测试
- `tests/test_recommender.py` - 推荐器测试
- `tests/test_integration.py` - 集成测试

**使用方式**:
```bash
cd stock_analyzer
.venv\Scripts\python recommendation_cli.py
```

**执行选项:**

1. **Subagent-Driven (本会话)** - 我派生子代理逐个执行任务，任务间代码审查，快速迭代
2. **Parallel Session (新会话)** - 在新会话中使用 executing-plans 批量执行

请选择执行方式？