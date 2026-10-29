"""Точка входа: запуск интерактивного эмулятора."""

from __future__ import annotations

import importlib

from .shell import Shell


def enable_line_editing() -> None:
    """Включает редактирование строки и историю стрелками, если возможно."""
    try:
        importlib.import_module("readline")
    except ImportError:
        pass


def main() -> int:
    """Запускает эмулятор и возвращает код завершения."""
    enable_line_editing()
    return Shell().run()
