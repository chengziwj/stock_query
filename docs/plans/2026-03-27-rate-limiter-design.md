# 限流器设计文档

## 概述

为股票数据获取模块添加令牌桶限流器，防止请求过于频繁导致 IP 被封禁。

## 需求

- 全局单例限流器
- 令牌桶算法实现
- 速率：每秒 1 个令牌
- 桶容量：3 个令牌
- 阻塞式等待

## 设计

### 令牌桶算法

```
请求到达 -> 尝试获取令牌
              |
              v
         有令牌? --是--> 放行请求
              |
              否
              v
         等待令牌补充 -> 获取令牌 -> 放行请求
```

**参数**：
- `_rate = 1.0`：每秒补充 1 个令牌
- `_capacity = 3`：桶最大存储 3 个令牌
- `_tokens`：当前令牌数量（初始为 3）

**令牌补充逻辑**：
```
当前令牌数 = min(容量, 上次令牌数 + (当前时间 - 上次时间) * 速率)
```

### 类设计

```python
class _RateLimiter:
    """令牌桶限流器（全局单例）"""
    _instance = None

    def __new__(cls):
        # 单例模式：确保全局唯一实例
        ...

    def acquire(self, timeout: float = None) -> bool:
        """
        获取令牌

        Args:
            timeout: 最大等待时间（秒），None 表示无限等待

        Returns:
            True 表示获取成功，False 表示超时
        """
        ...
```

### 集成位置

在 `DataFetcher._fetch_with_akshare()` 方法开头调用：

```python
def _fetch_with_akshare(self, code: str, start_date: str, end_date: str):
    # 限流：获取令牌
    _RateLimiter().acquire()

    # 原有逻辑...
    df = ak.stock_zh_a_hist(...)
    return df
```

## 修改文件

| 文件 | 修改内容 |
|------|----------|
| `stock_analyzer/data_fetcher.py` | 新增 `_RateLimiter` 类，在请求前调用限流 |

## 测试

- 单元测试：验证令牌补充逻辑正确性
- 集成测试：验证多次请求间隔符合预期