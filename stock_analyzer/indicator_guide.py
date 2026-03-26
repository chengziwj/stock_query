"""指标解读模块 - 各技术指标的详细说明"""

INDICATOR_GUIDE = {
    "MA均线": {
        "name": "移动平均线 (Moving Average)",
        "calculation": "MA = N日收盘价之和 / N",
        "periods": "MA5(短期)、MA20(中期)、MA60(长期)",
        "signals": [
            "价格 > MA5 > MA20 > MA60：完美多头排列，强烈看涨",
            "价格 < MA5 < MA20 < MA60：完美空头排列，强烈看跌",
            "MA5上穿MA20：金叉，短期买入信号",
            "MA5下穿MA20：死叉，短期卖出信号",
            "价格在MA上方：该周期趋势向上",
            "价格在MA下方：该周期趋势向下"
        ],
        "tips": "MA周期越长，支撑/阻力作用越强。MA60常作为牛熊分界线。"
    },

    "RSI": {
        "name": "相对强弱指数 (Relative Strength Index)",
        "calculation": "RSI = 100 - 100/(1+RS)，RS=平均涨幅/平均跌幅",
        "range": "0-100",
        "signals": [
            "RSI > 80：严重超买，回调风险大",
            "RSI > 70：超买区域，注意风险",
            "RSI < 30：超卖区域，可能反弹",
            "RSI < 20：严重超卖，反弹概率高",
            "RSI > 50：多头占优",
            "RSI < 50：空头占优"
        ],
        "tips": "RSI背离是重要信号：价格创新高但RSI不创新高=顶背离；价格创新低但RSI不创新低=底背离。"
    },

    "MACD": {
        "name": "指数平滑异同移动平均线 (Moving Average Convergence Divergence)",
        "calculation": "DIF=EMA12-EMA26，DEA=DIF的EMA9，MACD=(DIF-DEA)×2",
        "signals": [
            "DIF上穿DEA：金叉，买入信号",
            "DIF下穿DEA：死叉，卖出信号",
            "MACD红柱增长：多头动能增强",
            "MACD绿柱增长：空头动能增强",
            "零轴上方金叉：强势买入信号",
            "零轴下方金叉：反弹买入信号"
        ],
        "tips": "MACD是滞后指标，适合确认趋势。配合KDJ使用效果更好：KDJ先发出信号，MACD确认。"
    },

    "BOLL": {
        "name": "布林带 (Bollinger Bands)",
        "calculation": "中轨=MA20，上轨=中轨+2σ，下轨=中轨-2σ",
        "signals": [
            "价格触及上轨：可能超买",
            "价格触及下轨：可能超卖",
            "价格突破上轨：强势特征",
            "价格跌破下轨：弱势特征",
            "布林带收窄：即将变盘",
            "布林带扩张：趋势确立"
        ],
        "tips": "布林带宽度反映波动率。窄带突破往往伴随大行情。"
    },

    "KDJ": {
        "name": "随机指标 (Stochastic Oscillator)",
        "calculation": "K=RSV的3日平均，D=K的3日平均，J=3K-2D",
        "range": "K、D: 0-100，J: 可超100或低于0",
        "signals": [
            "K > D：看涨",
            "K < D：看跌",
            "K、D > 80：超买区域",
            "K、D < 20：超卖区域",
            "J > 100：严重超买",
            "J < 0：严重超卖",
            "K线上穿D线：金叉买入",
            "K线下穿D线：死叉卖出"
        ],
        "tips": "KDJ反应灵敏，适合短线。高位死叉卖出可靠，低位金叉买入可靠。J线领先K、D线。"
    },

    "WR": {
        "name": "威廉指标 (Williams %R)",
        "calculation": "WR = (N日最高-收盘价)/(N日最高-N日最低)×100",
        "range": "-100 到 0（通常显示为负值）",
        "signals": [
            "WR < -80（即>-80）：超买区域",
            "WR > -20（即<-20）：超卖区域",
            "WR从超买区回落：卖出信号",
            "WR从超卖区回升：买入信号"
        ],
        "tips": "WR与KDJ类似，但计算方式相反。WR对短期波动更敏感，建议结合其他指标使用。"
    },

    "CCI": {
        "name": "顺势指标 (Commodity Channel Index)",
        "calculation": "CCI = (TP-TP均值)/(0.015×TP平均偏差)，TP=(高+低+收)/3",
        "range": "无上下限，通常在-200到+200之间",
        "signals": [
            "CCI > +100：超买，多头市场",
            "CCI < -100：超卖，可能反弹",
            "CCI上穿+100：买入信号",
            "CCI下穿+100：卖出信号",
            "CCI上穿-100：抄底信号"
        ],
        "tips": "CCI适合捕捉趋势拐点。当CCI从高位回落时，即使价格还在上涨，也需警惕。"
    },

    "DMI": {
        "name": "动向指标 (Directional Movement Index)",
        "calculation": "+DI、-DI、ADX、ADXR",
        "signals": [
            "+DI > -DI：多头市场",
            "+DI < -DI：空头市场",
            "ADX > 25：趋势明确",
            "ADX < 20：震荡市场",
            "+DI上穿-DI且ADX上升：买入信号",
            "-DI上穿+DI且ADX上升：卖出信号"
        ],
        "tips": "ADX只反映趋势强度，不反映方向。ADX > 40后回落可能预示趋势结束。"
    },

    "OBV": {
        "name": "能量潮 (On Balance Volume)",
        "calculation": "OBV = 前日OBV ± 今日成交量（涨加跌减）",
        "signals": [
            "OBV上升+价格上升：趋势确认，继续看涨",
            "OBV下降+价格下降：趋势确认，继续看跌",
            "OBV上升+价格下降：底背离，可能见底",
            "OBV下降+价格上升：顶背离，可能见顶"
        ],
        "tips": "OBV是先行指标，背离信号往往提前于价格转折。"
    },

    "BBI": {
        "name": "多空指标 (Bull and Bear Index)",
        "calculation": "BBI = (MA3+MA6+MA12+MA24)/4",
        "signals": [
            "价格 > BBI：多头市场，持股为主",
            "价格 < BBI：空头市场，持币为主",
            "价格上穿BBI：买入信号",
            "价格下穿BBI：卖出信号"
        ],
        "tips": "BBI综合了多个周期均线，能有效判断多空状态。适合作为持仓/空仓的参考。"
    },

    "ATR": {
        "name": "真实波幅 (Average True Range)",
        "calculation": "TR=max(高-低,|高-昨收|,|低-昨收|)，ATR=TR的N日平均",
        "signals": [
            "ATR上升：波动加剧",
            "ATR下降：波动收窄",
            "止损设置：买入价 - 2×ATR",
            "目标设置：买入价 + 3×ATR"
        ],
        "tips": "ATR不判断方向，只反映波动性。高ATR时止损要放宽，低ATR时止损可收紧。"
    },

    "PSY": {
        "name": "心理线 (Psychological Line)",
        "calculation": "PSY = N日上涨天数/N×100",
        "range": "0-100",
        "signals": [
            "PSY > 75：超买，市场情绪过热",
            "PSY < 25：超卖，市场情绪低迷",
            "PSY > 90：严重过热，警惕见顶",
            "PSY < 10：严重低迷，可能见底"
        ],
        "tips": "PSY反映市场情绪，极端值往往预示反转。"
    },

    "成交量": {
        "name": "成交量分析 (Volume Analysis)",
        "signals": [
            "放量上涨：买盘积极，看涨",
            "缩量上涨：上涨乏力，需警惕",
            "放量下跌：恐慌抛售，看跌",
            "缩量下跌：卖压减轻，可能见底",
            "量价背离：警惕趋势反转"
        ],
        "tips": "量在价先，成交量是价格的先行指标。天量见天价，地量见地价。"
    }
}


def print_indicator_guide(indicator_name: str = None):
    """
    打印指标解读

    Args:
        indicator_name: 指标名称，为None时打印所有指标
    """
    if indicator_name:
        key = indicator_name.upper()
        for k, v in INDICATOR_GUIDE.items():
            if k.upper() == key or v["name"].upper().find(key) >= 0:
                _print_single_indicator(k, v)
                return
        print(f"未找到指标: {indicator_name}")
        print(f"可用指标: {', '.join(INDICATOR_GUIDE.keys())}")
    else:
        print("\n" + "=" * 60)
        print("           技术指标解读大全")
        print("=" * 60)
        for name, info in INDICATOR_GUIDE.items():
            _print_single_indicator(name, info)
            print()


def _print_single_indicator(name: str, info: dict):
    """打印单个指标信息"""
    print(f"\n【{name}】{info['name']}")
    print("-" * 50)

    if "calculation" in info:
        print(f"计算公式: {info['calculation']}")

    if "range" in info:
        print(f"数值范围: {info['range']}")

    if "periods" in info:
        print(f"常用周期: {info['periods']}")

    print("\n信号解读:")
    for signal in info["signals"]:
        print(f"  - {signal}")

    print(f"\n使用技巧: {info['tips']}")


def get_quick_reference() -> str:
    """
    获取快速参考卡片
    """
    lines = []
    lines.append("\n" + "=" * 60)
    lines.append("           技术指标快速参考卡")
    lines.append("=" * 60)

    lines.append("\n【超买超卖判断】")
    lines.append("  RSI > 70 或 KDJ.K > 80 或 WR < -80 → 超买，注意回调")
    lines.append("  RSI < 30 或 KDJ.K < 20 或 WR > -20 → 超卖，可能反弹")

    lines.append("\n【趋势方向判断】")
    lines.append("  MA多头排列(价>MA5>MA20>MA60) → 强烈看涨")
    lines.append("  MA空头排列(价<MA5<MA20<MA60) → 强烈看跌")
    lines.append("  价格 > BBI → 多头市场")
    lines.append("  +DI > -DI → 多头优势")

    lines.append("\n【买卖信号】")
    lines.append("  MACD金叉 + 零轴上方 → 强势买入")
    lines.append("  KDJ低位金叉(J<20) → 抄底买入")
    lines.append("  MACD死叉 + 零轴下方 → 强势卖出")

    lines.append("\n【趋势强度】")
    lines.append("  ADX > 25 → 趋势明确，顺势操作")
    lines.append("  ADX < 20 → 震荡行情，高抛低吸")

    lines.append("\n【量价关系】")
    lines.append("  放量上涨 → 买盘积极，继续持有")
    lines.append("  顶背离(价涨OBV跌) → 警惕见顶")
    lines.append("  底背离(价跌OBV涨) → 警惕见底")

    lines.append("\n【止损设置】")
    lines.append("  动态止损 = 买入价 - 2×ATR")
    lines.append("  支撑位止损 = 支撑位 × 0.97")

    lines.append("\n" + "=" * 60)

    return "\n".join(lines)


def print_all_indicators_summary():
    """打印所有指标概览"""
    print("\n" + "=" * 60)
    print("           支持的技术指标列表")
    print("=" * 60)

    categories = {
        "基础趋势指标": ["MA均线", "MACD", "BOLL"],
        "动量超买超卖指标": ["RSI", "KDJ", "WR", "CCI"],
        "趋势强度指标": ["DMI", "BBI"],
        "成交量指标": ["OBV", "成交量"],
        "波动率指标": ["ATR", "PSY"]
    }

    for category, indicators in categories.items():
        print(f"\n【{category}】")
        for ind in indicators:
            if ind in INDICATOR_GUIDE:
                print(f"  {ind}: {INDICATOR_GUIDE[ind]['name']}")

    print("\n使用方法: 输入 'help:指标名' 查看详细解读")
    print("例如: help:KDJ 或 help:MACD")
    print("=" * 60)