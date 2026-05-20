# Stock Query REPL with History Tab-Completion

**Date**: 2026-05-20
**Status**: Approved

## Overview

Add an interactive REPL mode to the stock_query CLI that remembers previously queried stocks and supports Tab-completion from history.

## Architecture

### New file: `repl.py`

- `ReplSession` class — manages readline configuration, history file I/O, and the interaction loop
- `HistoryStore` — reads/writes `~/.stock_query_history`, maintains deduplicated LRU list (max 100 entries)
- Format: `code name` per line (e.g. `000001 平安银行`)

### Modified: `cli.py`

- Add `repl` subcommand to argparse

## REPL Interaction

| Input | Behavior |
|---|---|
| `<code>` + Enter | Runs query (same pipeline as `query` command) |
| Tab key | Completes code from history, showing code + name |
| `help` | Prints usage help |
| `history` | Lists recent query history |
| `clear` | Clears history file |
| `quit` / Ctrl+D | Exits REPL |

## Dependencies

No new dependencies. Uses `readline` (stdlib) for Tab completion and `os.path` for history file.

## Example

```
$ python3 -m stock_query repl
> 000001<Tab>
000001  平安银行
600000  浦发银行
00700   腾讯控股
> 000001<Enter>
（展示平安银行行情）
> quit
```
