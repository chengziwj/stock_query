"""Interactive curses-based multi-select picker for stock history."""
from __future__ import annotations

import curses
from typing import NamedTuple


class Entry(NamedTuple):
    code: str
    name: str


def pick(entries: list[tuple[str, str]]) -> list[str]:
    """Open an interactive picker. Returns selected stock codes, or empty list on cancel."""
    if not entries:
        return []

    items = [Entry(c, n) for c, n in entries]
    return _curses_loop(items)


def _curses_loop(items: list[Entry]) -> list[str]:
    """Run the curses main loop. Uses A_REVERSE / A_BOLD for portability (no color)."""
    try:
        stdscr = curses.initscr()
    except Exception:
        # Terminal doesn't support curses — fall back gracefully
        return []

    try:
        curses.noecho()
        curses.cbreak()
        curses.curs_set(0)
        stdscr.keypad(True)

        selected = set()
        cursor = 0
        max_rows = curses.LINES - 4

        while True:
            stdscr.erase()

            # Header
            try:
                stdscr.addstr(1, 2, "Select stocks to query",
                              curses.A_BOLD)
                stdscr.addstr("  —  ↑↓ move  Space mark  Enter confirm  q quit")
            except curses.error:
                pass

            # Scroll window if needed
            scroll = 0
            if cursor >= max_rows:
                scroll = cursor - max_rows + 1

            visible = items[scroll : scroll + max_rows]
            for i, entry in enumerate(visible):
                real_idx = scroll + i
                y = 3 + i
                mark = "[x]" if real_idx in selected else "[ ]"
                line = f"  {real_idx + 1:>3}. {mark} {entry.code:<12} {entry.name}"

                if real_idx == cursor:
                    try:
                        stdscr.addstr(y, 2, line, curses.A_REVERSE)
                    except curses.error:
                        stdscr.addstr(y, 2, line)
                elif real_idx in selected:
                    try:
                        stdscr.addstr(y, 2, line, curses.A_BOLD)
                    except curses.error:
                        stdscr.addstr(y, 2, line)
                else:
                    stdscr.addstr(y, 2, line)

            # Footer
            footer_y = 3 + len(visible) + 1
            hint = "↑↓:move  Space:mark  Enter:query  q:quit  a:select-all  d:deselect-all"
            try:
                stdscr.addstr(footer_y, 2, hint, curses.A_DIM)
            except curses.error:
                pass

            stdscr.refresh()

            key = stdscr.getch()

            if key == ord("q"):
                return []
            elif key == curses.KEY_UP:
                cursor = max(0, cursor - 1)
            elif key == curses.KEY_DOWN:
                cursor = min(len(items) - 1, cursor + 1)
            elif key == ord(" "):
                if cursor in selected:
                    selected.discard(cursor)
                else:
                    selected.add(cursor)
            elif key == ord("a"):
                selected = set(range(len(items)))
            elif key == ord("d"):
                selected.clear()
            elif key in (curses.KEY_ENTER, 10, 13):  # Enter
                if selected:
                    return [items[i].code for i in sorted(selected)]
            elif key == curses.KEY_RESIZE:
                max_rows = curses.LINES - 4
    finally:
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.curs_set(1)
        curses.endwin()
