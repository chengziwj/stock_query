"""Entry point for python -m stock_query."""
import sys

if __name__ == "__main__":
    try:
        from stock_query.cli import main
        main()
    except ImportError:
        print("stock_query: not yet implemented.", file=sys.stderr)
        sys.exit(1)
