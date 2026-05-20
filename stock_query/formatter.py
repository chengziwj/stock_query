"""Rich-based output formatting for stock quotes."""
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

NUMERIC_FIELDS = {
    "price", "prev_close", "open", "high", "low",
    "high_limit", "low_limit",
}
VOLUME_FIELDS = {"volume", "volume_total"}
AMOUNT_FIELDS = {"amount", "market_cap", "total_market_cap"}
PCT_FIELDS = {"change_pct", "turnover", "amplitude"}

CARD_FIELDS = [
    ("name", "名称"),
    ("code", "代码"),
    ("price", "最新价"),
    ("change", "涨跌额"),
    ("change_pct", "涨跌幅"),
    ("open", "今开"),
    ("prev_close", "昨收"),
    ("high", "最高"),
    ("low", "最低"),
    ("volume_total", "成交量(手)"),
    ("amount", "成交额(万)"),
    ("turnover", "换手率"),
    ("pe_ratio", "市盈率"),
    ("amplitude", "振幅"),
    ("market_cap", "流通市值"),
]

TABLE_FIELDS = [
    ("name", "名称"),
    ("code", "代码"),
    ("price", "最新价"),
    ("change_pct", "涨跌幅"),
    ("volume_total", "成交量(手)"),
    ("turnover", "换手率"),
    ("pe_ratio", "市盈率"),
]


def format_value(field: str, value: str) -> str:
    """Format a single field value for display."""
    if not value or value == "0" or value == "0.00":
        return "-"

    try:
        if field in NUMERIC_FIELDS:
            return f"{float(value):.2f}"

        if field in PCT_FIELDS:
            v = float(value)
            sign = "+" if v > 0 else ""
            return f"{sign}{v:.2f}%"

        if field in VOLUME_FIELDS or field in AMOUNT_FIELDS:
            v = int(float(value))
            return f"{v:,}"

        if field == "change":
            v = float(value)
            sign = "+" if v > 0 else ""
            return f"{sign}{v:.2f}"

    except (ValueError, TypeError):
        return value

    return value


def _color_for_change(change_str: str) -> str:
    """Return 'red' for positive, 'green' for negative."""
    try:
        v = float(change_str)
        return "red" if v > 0 else "green" if v < 0 else "white"
    except (ValueError, TypeError):
        return "white"


def _render_card(stocks: List[Dict]) -> None:
    """Render single stock as a vertical card."""
    stock = stocks[0]
    name = stock.get("name", "?")
    code = stock.get("code", "?")
    console.print(f"\n[bold cyan]{name}[/bold cyan] ({code})", justify="center")
    console.print("─" * 40, style="dim")

    for key, label in CARD_FIELDS:
        raw = stock.get(key, "")
        if key in ("change_pct", "change"):
            color = _color_for_change(raw)
            val = format_value(key, raw)
            console.print(f"  {label}: [{color}]{val}[/{color}]")
        else:
            console.print(f"  {label}: {format_value(key, raw)}")
    console.print()


def _render_table(stocks: List[Dict]) -> None:
    """Render multiple stocks as a Rich table."""
    table = Table(box=box.SIMPLE_HEAD, expand=False)
    table.add_column("#", style="dim", width=3)

    for _, label in TABLE_FIELDS:
        justify = "right" if _ != "name" else "left"
        table.add_column(label, justify=justify)

    for i, stock in enumerate(stocks, 1):
        change = stock.get("change_pct", "")
        color = _color_for_change(change)

        row = [str(i)]
        for key, _ in TABLE_FIELDS:
            val = format_value(key, stock.get(key, ""))

            if key in ("change_pct", "change"):
                row.append(f"[{color}]{val}[/{color}]")
            else:
                row.append(val if val else "-")

        table.add_row(*row)

    console.print()
    console.print(table)
    console.print()


def format_quotes(stocks: List[Dict]) -> None:
    """Render stock quotes to terminal. Single stock → card, batch → table."""
    if not stocks:
        console.print("[dim]No data to display.[/dim]")
        return

    if len(stocks) == 1:
        _render_card(stocks)
    else:
        _render_table(stocks)
