"""A股股票分析程序 - 主程序入口"""

import sys
import io
from datetime import datetime

# 设置Windows控制台UTF-8编码
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from data_fetcher import fetch_stock_data, DataFetcher
from technical_indicators import calculate_all_indicators, get_latest_values
from trend_analyzer import get_trend_analysis, Trend
from support_resistance import get_support_resistance_analysis
from volume_price import get_volume_price_analysis
from price_prediction import get_price_prediction
from indicator_guide import print_indicator_guide, get_quick_reference, print_all_indicators_summary
from console_ui import (
    Colors, colorize, draw_box, draw_section,
    format_price_change, format_trend, format_risk, format_indicator_value,
    print_welcome, print_goodbye, pad_to_width
)


def format_output(
    df,
    standard_code: str,
    stock_name: str,
    indicators: dict,
    latest: dict,
    analysis: dict,
    sr_analysis: dict,
    vp_analysis: dict,
    prediction: dict
) -> str:
    """格式化输出结果"""
    lines = []

    # ===== 价格信息 =====
    last_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2] if len(df) > 1 else last_close
    change_pct = ((last_close - prev_close) / prev_close) * 100 if prev_close else 0
    volume = df['vol'].iloc[-1]

    price_lines = []
    price_lines.append(f"当前价格: {colorize(f'{last_close:.2f}', Colors.BRIGHT_CYAN + Colors.BOLD)} 元")
    price_lines.append(f"涨跌幅:   {format_price_change(change_pct)}")

    if volume >= 100000000:
        vol_str = f"{volume/100000000:.2f}亿股"
    elif volume >= 10000:
        vol_str = f"{volume/10000:.2f}万股"
    else:
        vol_str = f"{volume:.0f}股"
    price_lines.append(f"成交量:   {colorize(vol_str, Colors.CYAN)}")

    lines.append(draw_section("价格信息", '\n'.join(price_lines)))

    # ===== 价格预测 =====
    pred = prediction['prediction']
    pred_lines = []

    # 方向颜色
    if pred['direction'] == '上涨':
        dir_color = Colors.BRIGHT_RED
    elif pred['direction'] == '下跌':
        dir_color = Colors.BRIGHT_GREEN
    else:
        dir_color = Colors.BRIGHT_YELLOW

    pred_lines.append(f"预测方向: {colorize(pred['direction'], dir_color + Colors.BOLD)}  概率: {pred['probability']}%")
    target_price_str = f"{pred['target_price']:.2f}"
    pred_lines.append(f"目标价格: {colorize(target_price_str, Colors.BRIGHT_CYAN)} 元  时间: {pred['time_frame']}")
    pred_lines.append(f"置信度:   {colorize(pred['confidence'], Colors.BRIGHT_YELLOW if pred['confidence'] == '高' else Colors.WHITE)}")

    # 价格区间
    pr = prediction['price_range']
    pred_lines.append(f"短期目标: {pr['targets']['short_term']:.2f}  中期: {pr['targets']['medium_term']:.2f}  长期: {pr['targets']['long_term']:.2f}")

    lines.append("")
    lines.append(draw_section("价格预测", '\n'.join(pred_lines)))

    # ===== 量价关系 =====
    vp_lines = []

    # 量价形态
    vp_color = Colors.BRIGHT_RED if vp_analysis['signal'] == 'bullish' else Colors.BRIGHT_GREEN if vp_analysis['signal'] == 'bearish' else Colors.WHITE
    vp_lines.append(f"量价形态: {colorize(vp_analysis['pattern'], vp_color)}  强度: {'★' * vp_analysis['strength']}{'☆' * (5 - vp_analysis['strength'])}")
    vp_lines.append(f"量比: {vp_analysis['volume_ratio']:.2f}  成交量趋势: {vp_analysis['volume_trend']}")

    # 资金流向
    mf = vp_analysis['money_flow']
    flow_color = Colors.BRIGHT_RED if mf['flow_signal'] == 'bullish' else Colors.BRIGHT_GREEN if mf['flow_signal'] == 'bearish' else Colors.WHITE
    vp_lines.append(f"资金流向: {colorize(mf['flow_status'], flow_color)}  MFI: {mf['mfi']:.1f}")

    # 极端成交量检测
    if vp_analysis.get('extreme_volume', {}).get('detected'):
        ev = vp_analysis['extreme_volume']
        ev_color = Colors.BRIGHT_RED if ev['signal'] == 'bearish' else Colors.BRIGHT_GREEN
        vp_lines.append(f"特殊信号: {colorize(ev['pattern'], ev_color + Colors.BOLD)} - {ev['description']}")

    lines.append("")
    lines.append(draw_section("量价关系", '\n'.join(vp_lines)))

    # ===== 基础技术指标 =====
    base_lines = []
    ma_str = f"MA5: {latest['ma']['MA5']:.2f}  MA10: {latest['ma']['MA10']:.2f}  MA20: {latest['ma']['MA20']:.2f}"
    if latest['ma']['MA60']:
        ma_str += f"  MA60: {latest['ma']['MA60']:.2f}"
    base_lines.append(ma_str)

    rsi_colored = format_indicator_value(latest['rsi'], 'rsi')
    base_lines.append(f"RSI(14): {rsi_colored}")

    macd_val = latest['macd']['MACD']
    macd_color = Colors.BRIGHT_RED if macd_val > 0 else Colors.BRIGHT_GREEN
    base_lines.append(f"MACD: {colorize(f'{macd_val:.4f}', macd_color)}")

    base_lines.append(f"布林带: 上{latest['bollinger']['upper']:.2f} / 中{latest['bollinger']['middle']:.2f} / 下{latest['bollinger']['lower']:.2f}")

    lines.append("")
    lines.append(draw_section("基础技术指标", '\n'.join(base_lines)))

    # ===== 动量指标 =====
    momentum_lines = []

    k_colored = format_indicator_value(latest['kdj']['K'], 'kdj_k')
    j_colored = format_indicator_value(latest['kdj']['J'], 'kdj_j')
    kdj_status = colorize("超买", Colors.BRIGHT_RED) if latest['kdj']['K'] > 80 else colorize("超卖", Colors.BRIGHT_GREEN) if latest['kdj']['K'] < 20 else ""
    momentum_lines.append(f"KDJ: K={k_colored}  D={latest['kdj']['D']:.1f}  J={j_colored}  {kdj_status}")

    wr_status = colorize("超买", Colors.BRIGHT_RED) if latest['wr'] < -80 else colorize("超卖", Colors.BRIGHT_GREEN) if latest['wr'] > -20 else ""
    momentum_lines.append(f"WR(14): {latest['wr']:.1f}  {wr_status}")

    cci_status = colorize("多头", Colors.BRIGHT_RED) if latest['cci'] > 100 else colorize("超卖", Colors.BRIGHT_GREEN) if latest['cci'] < -100 else ""
    momentum_lines.append(f"CCI(20): {latest['cci']:.1f}  {cci_status}")

    lines.append("")
    lines.append(draw_section("动量指标", '\n'.join(momentum_lines)))

    # ===== 趋势指标 =====
    trend_lines = []

    dmi_status = colorize("多头", Colors.BRIGHT_RED) if latest['dmi']['+DI'] > latest['dmi']['-DI'] else colorize("空头", Colors.BRIGHT_GREEN)
    adx_status = colorize("趋势明确", Colors.BRIGHT_YELLOW) if latest['dmi']['ADX'] > 25 else colorize("震荡", Colors.WHITE)
    trend_lines.append(f"DMI: +DI={latest['dmi']['+DI']:.1f}  -DI={latest['dmi']['-DI']:.1f}  ADX={latest['dmi']['ADX']:.1f}  ({dmi_status}, {adx_status})")

    bbi_status = colorize("多头", Colors.BRIGHT_RED) if last_close > latest['bbi'] else colorize("空头", Colors.BRIGHT_GREEN)
    trend_lines.append(f"BBI: {latest['bbi']:.2f}元  ({bbi_status})")

    lines.append("")
    lines.append(draw_section("趋势指标", '\n'.join(trend_lines)))

    # ===== 支撑阻力位 =====
    current_price = sr_analysis['current_price']

    sr_lines = []

    if sr_analysis['nearest_support']:
        ns = sr_analysis['nearest_support']
        distance = (current_price - ns.price) / current_price * 100
        sr_lines.append(f"最近支撑: {colorize(f'{ns.price:.2f}', Colors.BRIGHT_GREEN)}元 ({ns.level_type}) 距离-{distance:.1f}%")

    sr_lines.append("支撑位:")
    for s in sr_analysis['supports'][:3]:
        strength_bar = colorize("*" * s.strength, Colors.BRIGHT_GREEN)
        sr_lines.append(f"  {s.price:.2f}元 [{strength_bar}] {s.level_type}")

    if sr_analysis['nearest_resistance']:
        nr = sr_analysis['nearest_resistance']
        distance = (nr.price - current_price) / current_price * 100
        sr_lines.append(f"最近阻力: {colorize(f'{nr.price:.2f}', Colors.BRIGHT_RED)}元 ({nr.level_type}) 距离+{distance:.1f}%")

    sr_lines.append("阻力位:")
    for r in sr_analysis['resistances'][:3]:
        strength_bar = colorize("*" * r.strength, Colors.BRIGHT_RED)
        sr_lines.append(f"  {r.price:.2f}元 [{strength_bar}] {r.level_type}")

    lines.append("")
    lines.append(draw_section("支撑位与阻力位", '\n'.join(sr_lines)))

    # ===== 趋势分析 =====
    trend_analysis_lines = []

    trend_colored = format_trend(analysis['trend_text'])
    trend_analysis_lines.append(f"综合判断: {trend_colored}")

    signals = analysis['signals']
    bullish_count = sum(1 for v in signals.values() if v == 1)
    bearish_count = sum(1 for v in signals.values() if v == -1)
    neutral_count = sum(1 for v in signals.values() if v == 0)
    trend_analysis_lines.append(f"信号统计: {colorize(f'看涨{bullish_count}项', Colors.BRIGHT_RED)} / {colorize(f'看跌{bearish_count}项', Colors.BRIGHT_GREEN)} / 中性{neutral_count}项")

    trend_analysis_lines.append("判断理由:")
    for i, reason in enumerate(analysis['reasons'][:5], 1):
        trend_analysis_lines.append(f"  {i}. {reason}")

    lines.append("")
    lines.append(draw_section("趋势分析", '\n'.join(trend_analysis_lines)))

    # ===== 买入建议 =====
    buy_lines = []

    if sr_analysis['buy_suggestions']:
        for i, suggestion in enumerate(sr_analysis['buy_suggestions'][:3], 1):
            buy_lines.append(f"{i}. 买入价: {colorize(f'{suggestion.price:.2f}', Colors.BRIGHT_CYAN)}元")
            buy_lines.append(f"   理由: {suggestion.reason}")
            buy_lines.append(f"   风险: {format_risk(suggestion.risk_level)}  止损: {colorize(f'{suggestion.stop_loss:.2f}', Colors.BRIGHT_GREEN)}元  目标: {colorize(f'{suggestion.target_price:.2f}', Colors.BRIGHT_RED)}元")
    else:
        buy_lines.append("暂无明确买入信号，建议观望")

    lines.append("")
    lines.append(draw_section("买入建议", '\n'.join(buy_lines)))

    # ===== 风险提示 =====
    lines.append("")
    lines.append(colorize("  [风险提示]", Colors.BRIGHT_YELLOW))
    lines.append(colorize(f"  {pred['risk_warning']}", Colors.DIM))
    lines.append(colorize("  本分析仅供参考，不构成投资建议。投资有风险，入市需谨慎。", Colors.DIM))

    return '\n'.join(lines)


def analyze_stock(stock_code: str) -> None:
    """分析指定股票"""
    try:
        print()
        print(colorize("  正在获取数据...", Colors.CYAN))

        # 获取数据
        df, standard_code, stock_name = fetch_stock_data(stock_code)

        print(colorize(f"  分析中: {standard_code} ({stock_name})...", Colors.CYAN))
        print()

        # 计算技术指标
        indicators = calculate_all_indicators(df)
        latest = get_latest_values(indicators, df)

        # 趋势分析
        analysis = get_trend_analysis(df, indicators)

        # 支撑阻力分析
        sr_analysis = get_support_resistance_analysis(df, indicators, analysis)

        # 量价分析
        vp_analysis = get_volume_price_analysis(df, indicators)

        # 价格预测
        prediction = get_price_prediction(df, indicators, sr_analysis, vp_analysis)

        # 构建标题
        start_date = df['trade_date'].iloc[0].strftime('%Y-%m-%d')
        end_date = df['trade_date'].iloc[-1].strftime('%Y-%m-%d')

        title = f"{standard_code} {stock_name} | {start_date} ~ {end_date}"

        # 输出结果
        output = format_output(df, standard_code, stock_name, indicators, latest, analysis, sr_analysis, vp_analysis, prediction)
        print(draw_box(title, output, width=70, style="double"))

        print()
        print(colorize("  提示: help 查看指标解读 | help:指标名 查看单个指标", Colors.DIM))

    except ValueError as e:
        print()
        print(colorize(f"  错误: {e}", Colors.BRIGHT_RED))
        print(colorize("  支持格式: 000001 | 600000.SS | 平安银行", Colors.DIM))

    except RuntimeError as e:
        print()
        print(colorize(f"  数据获取失败: {e}", Colors.BRIGHT_RED))

    except Exception as e:
        print()
        print(colorize(f"  发生错误: {e}", Colors.BRIGHT_RED))
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print_welcome()

    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
        analyze_stock(stock_code)
    else:
        while True:
            print()
            user_input = input(colorize("  > ", Colors.BRIGHT_CYAN)).strip()

            if user_input.lower() in ('q', 'quit', 'exit'):
                print_goodbye()
                break

            if user_input.lower() in ('help', '帮助', '?'):
                print_all_indicators_summary()
                continue

            if user_input.lower().startswith('help:'):
                indicator = user_input[5:].strip()
                print_indicator_guide(indicator)
                continue

            if user_input.lower() in ('ref', '参考'):
                print(get_quick_reference())
                continue

            if user_input.lower() in ('cls', 'clear', '清屏'):
                from console_ui import print_clear_screen
                print_clear_screen()
                print_welcome()
                continue

            if not user_input:
                continue

            analyze_stock(user_input)


if __name__ == "__main__":
    main()