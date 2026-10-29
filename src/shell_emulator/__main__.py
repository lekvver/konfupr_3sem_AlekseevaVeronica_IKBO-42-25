"""Запуск эмулятора командой python -m shell_emulator."""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
