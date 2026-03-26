"""命令行美化模块 - 颜色输出和方框绘制"""

import re

# ANSI颜色代码
class Colors:
    """终端颜色"""
    # 基础颜色
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 亮色
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'

    # 背景色
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


def colorize(text: str, color: str) -> str:
    """给文本添加颜色"""
    return f"{color}{text}{Colors.RESET}"


def strip_ansi(text: str) -> str:
    """移除ANSI转义序列"""
    ansi_pattern = re.compile(r'\033\[[0-9;]*m')
    return ansi_pattern.sub('', text)


def get_display_width(text: str) -> int:
    """
    计算字符串的显示宽度（中文算2个宽度，ANSI序列不计算）

    Args:
        text: 输入字符串

    Returns:
        显示宽度
    """
    # 先移除ANSI转义序列
    clean_text = strip_ansi(text)

    width = 0
    for char in clean_text:
        # 中文字符宽度为2
        if '\u4e00' <= char <= '\u9fff':
            width += 2
        # 中文标点符号宽度为2
        elif char in '，。！？、；：""''（）【】《》…—':
            width += 2
        # 全角字符
        elif '\uff00' <= char <= '\uffef':
            width += 2
        else:
            width += 1
    return width


def pad_to_width(text: str, target_width: int) -> str:
    """
    将文本填充到指定显示宽度

    Args:
        text: 输入文本（可能包含ANSI序列）
        target_width: 目标显示宽度

    Returns:
        填充后的文本
    """
    current_width = get_display_width(text)
    if current_width >= target_width:
        return text
    return text + ' ' * (target_width - current_width)


def draw_box(title: str, content: str, width: int = 66, style: str = "double") -> str:
    """
    绘制带标题的方框

    Args:
        title: 标题
        content: 内容
        width: 宽度
        style: 样式 (single/double/rounded)

    Returns:
        方框字符串
    """
    # 边框字符
    styles = {
        "double": {"tl": "╔", "tr": "╗", "bl": "╚", "br": "╝", "h": "═", "v": "║"},
        "single": {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│"},
        "rounded": {"tl": "╭", "tr": "╮", "bl": "╰", "br": "╯", "h": "─", "v": "│"},
    }

    s = styles.get(style, styles["double"])

    lines = []

    # 内容宽度（减去边框和空格）
    content_width = width - 4  # 左边框(1) + 右边框(1) + 左空格(1) + 右空格(1)

    # 标题行
    title_colored = colorize(f" {title} ", Colors.BRIGHT_CYAN)
    title_display_width = get_display_width(title_colored)
    title_padding = content_width - title_display_width + 2  # +2 是因为标题前后有 ═

    # 构建标题行：╔═ 标题 ═══...╗
    title_line = s["tl"] + s["h"] + title_colored + s["h"] * max(0, title_padding) + s["tr"]
    lines.append(title_line)

    # 内容行
    for line in content.split('\n'):
        # 填充到目标宽度
        padded_line = pad_to_width(line, content_width)
        lines.append(s["v"] + " " + padded_line + " " + s["v"])

    # 底部
    lines.append(s["bl"] + s["h"] * (width - 2) + s["br"])

    return '\n'.join(lines)


def draw_section(title: str, content: str) -> str:
    """
    绘制带标题的小节

    Args:
        title: 标题
        content: 内容

    Returns:
        小节字符串
    """
    lines = []

    # 标题行
    colored_title = colorize(f"【{title}】", Colors.BRIGHT_YELLOW + Colors.BOLD)
    lines.append(colored_title)

    # 内容
    for line in content.split('\n'):
        lines.append(f"  {line}")

    return '\n'.join(lines)


def draw_separator(width: int = 60, style: str = "double") -> str:
    """绘制分隔线"""
    styles = {
        "double": "═",
        "single": "─",
        "dashed": "╌",
        "dotted": "┄",
    }
    char = styles.get(style, "═")
    return colorize(char * width, Colors.CYAN)


def format_price_change(change_pct: float) -> str:
    """格式化涨跌幅，带颜色"""
    if change_pct > 0:
        return colorize(f"+{change_pct:.2f}%", Colors.BRIGHT_RED)
    elif change_pct < 0:
        return colorize(f"{change_pct:.2f}%", Colors.BRIGHT_GREEN)
    else:
        return colorize(f"{change_pct:.2f}%", Colors.WHITE)


def format_trend(trend_text: str) -> str:
    """格式化趋势判断，带颜色"""
    if "看涨" in trend_text:
        return colorize(trend_text, Colors.BRIGHT_RED + Colors.BOLD)
    elif "看跌" in trend_text:
        return colorize(trend_text, Colors.BRIGHT_GREEN + Colors.BOLD)
    else:
        return colorize(trend_text, Colors.BRIGHT_YELLOW + Colors.BOLD)


def format_risk(risk: str) -> str:
    """格式化风险等级"""
    if risk == "低":
        return colorize(risk, Colors.BRIGHT_GREEN)
    elif risk == "高":
        return colorize(risk, Colors.BRIGHT_RED)
    else:
        return colorize(risk, Colors.BRIGHT_YELLOW)


def format_indicator_value(value: float, indicator_type: str) -> str:
    """格式化指标值，根据类型添加颜色"""
    if indicator_type == "rsi":
        if value > 70:
            return colorize(f"{value:.1f}", Colors.BRIGHT_RED)
        elif value < 30:
            return colorize(f"{value:.1f}", Colors.BRIGHT_GREEN)
        else:
            return f"{value:.1f}"

    elif indicator_type == "kdj_k":
        if value > 80:
            return colorize(f"{value:.1f}", Colors.BRIGHT_RED)
        elif value < 20:
            return colorize(f"{value:.1f}", Colors.BRIGHT_GREEN)
        else:
            return f"{value:.1f}"

    elif indicator_type == "kdj_j":
        if value > 100:
            return colorize(f"{value:.1f}", Colors.BRIGHT_RED)
        elif value < 0:
            return colorize(f"{value:.1f}", Colors.BRIGHT_GREEN)
        else:
            return f"{value:.1f}"

    return f"{value:.1f}"


def print_clear_screen():
    """清屏"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def print_welcome():
    """打印欢迎信息"""
    print()
    print(colorize("  ╔══════════════════════════════════════════════════════╗", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "          " + colorize("A股股票分析程序 (增强版)", Colors.BRIGHT_YELLOW + Colors.BOLD) + "                    " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "  提示: help 查看指标解读 | help:KDJ 查看单个指标    " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ╚══════════════════════════════════════════════════════╝", Colors.BRIGHT_CYAN))
    print()


def print_goodbye():
    """打印告别信息"""
    print()
    print(colorize("  ╔═══════════════════════════════════════════════════╗", Colors.BRIGHT_CYAN))
    print(colorize("  ║", Colors.BRIGHT_CYAN) + "        " + colorize("感谢使用，祝投资顺利！", Colors.BRIGHT_YELLOW) + "                      " + colorize("║", Colors.BRIGHT_CYAN))
    print(colorize("  ╚═══════════════════════════════════════════════════╝", Colors.BRIGHT_CYAN))
    print()