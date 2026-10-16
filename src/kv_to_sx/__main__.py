"""Entrypoint when running `python -m kv_to_sx`."""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
