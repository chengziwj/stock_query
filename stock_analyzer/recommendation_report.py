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
