# Rate Limiter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a global token bucket rate limiter to prevent IP bans from excessive API requests.

**Architecture:** Singleton `_RateLimiter` class using token bucket algorithm. Tokens replenish at 1/second, max capacity 3. `DataFetcher._fetch_with_akshare()` acquires a token before each request, blocking if none available.

**Tech Stack:** Python stdlib only (threading, time) - no new dependencies.

---

### Task 1: Rate Limiter Unit Tests

**Files:**
- Create: `stock_analyzer/tests/test_rate_limiter.py`

**Step 1: Write the failing tests**

```python
"""限流器单元测试"""

import threading
import time
import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_fetcher import _RateLimiter


class TestRateLimiter:
    """令牌桶限流器测试"""

    def test_singleton_pattern(self):
        """测试单例模式：多次调用返回同一实例"""
        limiter1 = _RateLimiter()
        limiter2 = _RateLimiter()
        assert limiter1 is limiter2

    def test_initial_tokens(self):
        """测试初始状态：桶应满（3个令牌）"""
        limiter = _RateLimiter()
        # 重置状态用于测试
        limiter._tokens = 3.0
        limiter._last_time = time.time()

        assert limiter._tokens == 3.0

    def test_acquire_reduces_tokens(self):
        """测试获取令牌：每次获取减少令牌数"""
        limiter = _RateLimiter()
        limiter._tokens = 3.0
        limiter._last_time = time.time()

        limiter.acquire()
        assert limiter._tokens == 2.0

    def test_acquire_blocks_when_empty(self):
        """测试令牌不足时阻塞等待"""
        limiter = _RateLimiter()
        limiter._tokens = 0.0
        limiter._last_time = time.time()

        start = time.time()
        limiter.acquire()
        elapsed = time.time() - start

        # 应该等待约1秒（补充1个令牌）
        assert elapsed >= 0.9

    def test_tokens_replenish_over_time(self):
        """测试令牌随时间补充"""
        limiter = _RateLimiter()
        limiter._tokens = 0.0
        limiter._last_time = time.time() - 2.0  # 2秒前

        limiter._refill_tokens()
        # 2秒应补充2个令牌
        assert limiter._tokens == 2.0

    def test_tokens_cannot_exceed_capacity(self):
        """测试令牌数不超过桶容量"""
        limiter = _RateLimiter()
        limiter._tokens = 2.0
        limiter._last_time = time.time() - 10.0  # 很久之前

        limiter._refill_tokens()
        # 最多3个令牌
        assert limiter._tokens == 3.0

    def test_thread_safety(self):
        """测试线程安全：多线程并发获取令牌"""
        limiter = _RateLimiter()
        limiter._tokens = 3.0
        limiter._last_time = time.time()

        results = []
        errors = []

        def worker():
            try:
                limiter.acquire()
                results.append(threading.current_thread().name)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, name=f"t{i}")
            for i in range(5)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 5
```

**Step 2: Run test to verify it fails**

Run: `cd D:\py\stock\stock_analyzer && .venv\Scripts\python -m pytest tests/test_rate_limiter.py -v`
Expected: FAIL with "_RateLimiter not found" or similar

**Step 3: Commit**

```bash
git add stock_analyzer/tests/test_rate_limiter.py
git commit -m "test: add rate limiter unit tests"
```

---

### Task 2: Implement Rate Limiter

**Files:**
- Modify: `stock_analyzer/data_fetcher.py` (add at top after imports)

**Step 1: Implement _RateLimiter class**

Add after the imports (around line 9):

```python
import threading


class _RateLimiter:
    """
    令牌桶限流器（全局单例）

    防止请求过于频繁导致IP被封禁。
    - 每秒补充 1 个令牌
    - 桶容量 3 个令牌
    - 无令牌时阻塞等待
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._rate = 1.0          # 每秒1个令牌
                    instance._capacity = 3        # 桶容量
                    instance._tokens = 3.0        # 初始满桶
                    instance._last_time = time.time()
                    instance._inner_lock = threading.Lock()
                    cls._instance = instance
        return cls._instance

    def acquire(self, timeout: float = None) -> bool:
        """
        获取一个令牌

        Args:
            timeout: 最大等待时间（秒），None 表示无限等待

        Returns:
            True 表示获取成功，False 表示超时
        """
        deadline = None if timeout is None else time.time() + timeout

        while True:
            with self._inner_lock:
                self._refill_tokens()

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return True

            # 检查是否超时
            if deadline is not None and time.time() >= deadline:
                return False

            # 等待一小段时间再重试
            time.sleep(0.1)

    def _refill_tokens(self):
        """补充令牌（必须在锁内调用）"""
        now = time.time()
        elapsed = now - self._last_time

        # 按速率补充令牌
        new_tokens = elapsed * self._rate
        self._tokens = min(self._capacity, self._tokens + new_tokens)
        self._last_time = now
```

**Step 2: Run test to verify it passes**

Run: `cd D:\py\stock\stock_analyzer && .venv\Scripts\python -m pytest tests/test_rate_limiter.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add stock_analyzer/data_fetcher.py
git commit -m "feat: add token bucket rate limiter"
```

---

### Task 3: Integrate Rate Limiter into DataFetcher

**Files:**
- Modify: `stock_analyzer/data_fetcher.py` (method `_fetch_with_akshare`)

**Step 1: Add rate limiter call in _fetch_with_akshare**

Modify the `_fetch_with_akshare` method to call the rate limiter at the start:

```python
def _fetch_with_akshare(
    self,
    code: str,
    start_date: str,
    end_date: str
) -> Optional[pd.DataFrame]:
    """
    使用akshare获取日线数据

    Args:
        code: 6位股票代码
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD

    Returns:
        原始DataFrame或None
    """
    # 限流：获取令牌
    _RateLimiter().acquire()

    # 判断交易所
    exchange = StockCodeParser.get_exchange(code)

    # 使用akshare获取A股日线数据
    # akshare的stock_zh_a_hist接口
    symbol = code
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust=""  # 不复权
    )

    return df
```

**Step 2: Run existing tests to ensure no regression**

Run: `cd D:\py\stock\stock_analyzer && .venv\Scripts\python -m pytest tests/ -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add stock_analyzer/data_fetcher.py
git commit -m "feat: integrate rate limiter into DataFetcher"
```

---

### Task 4: Integration Test

**Files:**
- Create: `stock_analyzer/tests/test_rate_limiter_integration.py`

**Step 1: Write integration test**

```python
"""限流器集成测试"""

import time
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_fetcher import DataFetcher, _RateLimiter


class TestRateLimiterIntegration:
    """限流器与DataFetcher集成测试"""

    def test_multiple_requests_are_rate_limited(self):
        """测试多次请求受速率限制"""
        # 重置限流器状态
        limiter = _RateLimiter()
        limiter._tokens = 0.0
        limiter._last_time = time.time()

        fetcher = DataFetcher()

        # 记录连续请求的时间
        start = time.time()
        limiter.acquire()  # 第1次：等待约1秒
        t1 = time.time()
        limiter.acquire()  # 第2次：等待约1秒
        t2 = time.time()
        limiter.acquire()  # 第3次：等待约1秒
        t3 = time.time()

        # 验证间隔
        assert t1 - start >= 0.9  # 约1秒
        assert t2 - t1 >= 0.9     # 约1秒
        assert t3 - t2 >= 0.9     # 约1秒
```

**Step 2: Run integration test**

Run: `cd D:\py\stock\stock_analyzer && .venv\Scripts\python -m pytest tests/test_rate_limiter_integration.py -v`
Expected: PASS

**Step 3: Run all tests**

Run: `cd D:\py\stock\stock_analyzer && .venv\Scripts\python -m pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add stock_analyzer/tests/test_rate_limiter_integration.py
git commit -m "test: add rate limiter integration test"
```

---

### Task 5: Final Verification

**Step 1: Run all tests**

Run: `cd D:\py\stock\stock_analyzer && .venv\Scripts\python -m pytest tests/ -v`
Expected: All tests PASS

**Step 2: Manual verification with real stock data**

Run: `cd D:\py\stock\stock_analyzer && .venv\Scripts\python main.py 600519`
Expected: Normal output, takes about 1 second to fetch data

**Step 3: Push commits**

```bash
git push origin master
```