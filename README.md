# stock_query

基于腾讯财经行情接口的 Python 股票实时行情查询 CLI 工具。支持 A 股（沪深）、港股、美股。

## 安装

```bash
pip install -r stock_query/requirements.txt
```

依赖：`requests`（HTTP 请求）、`rich`（终端美化输出）。

## 用法

### 单次查询

```bash
# 单只股票
python3 -m stock_query query 000001

# 批量查询，逗号分隔
python3 -m stock_query query 000001,600000,00700,AAPL
```

代码前缀自动推断：

| 代码模式 | 市场 | 示例 |
|---------|------|-----|
| 000/002/300 开头 6 位 | 深市 | `000001` → 平安银行 |
| 600/601/603/688 开头 6 位 | 沪市 | `600000` → 浦发银行 |
| 0 开头 5 位 | 港股 | `00700` → 腾讯控股 |
| 纯字母 | 美股 | `AAPL` → Apple |

### 交互式 REPL（支持 Tab 历史补全）

```bash
python3 -m stock_query repl
```

进入交互模式后：
- 直接输入代码回车 → 查询行情
- 按 **Tab 键** → 弹出历史查询代码列表（支持代码/名称模糊匹配）
- `history` → 查看历史记录
- `clear` → 清空历史
- `help` → 查看帮助
- `quit` → 退出

## 输出示例

**单只股票（卡片模式）：**

```
                               平安银行 (000001)
────────────────────────────────────────
  名称: 平安银行
  代码: 000001
  最新价: 10.80
  涨跌额: -0.06
  涨跌幅: -0.55%
  今开: 10.86
  昨收: 10.86
  最高: 10.88
  最低: 10.78
  成交量(手): 430,092
  成交额(万): 46,571
  换手率: +0.22%
  市盈率: 4.87
  振幅: +0.92%
  流通市值: 2,095
```

**批量查询（表格模式）：**

```
  #  名称       代码     最新价   涨跌幅   成交量(手)   换手率   市盈率
 ──────────────────────────────────────────────────────────────────
  1  平安银行   000001    10.80   -0.55%      430,092   +0.22%     4.87
  2  浦发银行   600000     8.93   -0.22%      655,267   +0.20%     5.92
  3  腾讯控股   00700    458.20        -            -        -        -
```

涨为红色，跌为绿色。

## 项目结构

```
stock_query/
├── __init__.py        # 包入口
├── __main__.py        # python -m 入口
├── cli.py             # argparse CLI（query / repl 子命令）
├── fetcher.py         # HTTP 客户端，代码前缀推断
├── parser.py          # 腾讯 API 响应解析，按市场映射字段
├── formatter.py       # Rich 终端着色输出
├── repl.py            # 交互式 REPL + 历史管理
├── requirements.txt
└── tests/
    ├── test_fetcher.py
    ├── test_parser.py
    ├── test_formatter.py
    ├── test_cli.py
    ├── test_repl.py
    ├── test_integration.py   # 真实 API 集成测试
    └── conftest.py
```

## 运行测试

```bash
# 全部测试
python3 -m pytest stock_query/tests/ -v

# 跳过集成测试（离线环境）
python3 -m pytest stock_query/tests/ -v -m "not integration"
```

## 数据来源

腾讯财经公开行情接口 `qt.gtimg.cn`，覆盖沪深、港股、美股实时行情。
