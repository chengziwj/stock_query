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
