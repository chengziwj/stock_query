# A股股票分析程序

专为A股设计的股票技术分析工具，集成多项技术指标、量价分析和价格预测功能。

## 功能特性

- 📈 **价格预测** - 基于趋势强度和量价关系的智能预测
- 📊 **量价分析** - 量价形态识别、资金流向分析
- 🎯 **12项技术指标** - MA、RSI、MACD、KDJ、DMI 等
- 🔍 **支撑阻力识别** - 自动识别关键价格位
- 💡 **智能买入建议** - 买入点位、止损价、目标价
- 🎨 **美化命令行界面** - 彩色输出、方框布局

## 快速开始

### 安装依赖

```bash
cd stock_analyzer
uv venv
uv pip install -r requirements.txt
```

### 运行分析

```bash
# 命令行模式
.venv\Scripts\python main.py 600519    # 按代码查询
.venv\Scripts\python main.py 比亚迪     # 按中文名称查询

# 交互模式
.venv\Scripts\python main.py
```

## 技术指标

| 类别 | 指标 |
|------|------|
| 趋势 | MA均线、MACD、布林带、BBI |
| 动量 | RSI、KDJ、WR、CCI |
| 强度 | DMI（+DI/-DI/ADX） |
| 成交量 | OBV、量比、MFI |
| 波动率 | ATR、PSY |

## 输出示例

```
╔═ 002594.SZ 比亚迪 | 2025-09-22 ~ 2026-03-26 ══════════════════╗
║ 【价格预测】                                                 ║
║   预测方向: 上涨  概率: 75%                                  ║
║   目标价格: 107.66 元  时间: 1-3个交易日                     ║
║                                                              ║
║ 【量价关系】                                                 ║
║   量价形态: 缩量盘整  强度: ★★☆☆☆                            ║
║   资金流向: 资金平衡  MFI: 51.6                              ║
║                                                              ║
║ 【买入建议】                                                 ║
║   买入价: 102.32元  止损: 99.25元  目标: 104.22元            ║
╚══════════════════════════════════════════════════════════════╝
```

## 项目结构

```
stock_analyzer/
├── main.py                 # 主程序入口
├── data_fetcher.py         # 数据获取（akshare）
├── technical_indicators.py # 技术指标计算
├── trend_analyzer.py       # 趋势分析
├── support_resistance.py   # 支撑阻力分析
├── volume_price.py         # 量价关系分析
├── price_prediction.py     # 价格预测
├── console_ui.py           # 命令行美化
├── indicator_guide.py      # 指标解读帮助
└── tests/                  # 单元测试
```

## 依赖

- **akshare** - 股票数据获取（无需 API Key）
- **pandas** - 数据处理
- **numpy** - 数值计算

## 免责声明

本程序仅供学习研究使用，分析结果不构成任何投资建议。股市有风险，投资需谨慎。

## 许可证

MIT License