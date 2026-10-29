"""Точка входа: параметры командной строки и запуск эмулятора."""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Sequence

from .errors import ShellError
from .script import run_script
from .shell import Shell

EXIT_FAILURE = 1
NOT_SET = "<not set>"
DEBUG_PREFIX = "[debug]"


def build_parser() -> argparse.ArgumentParser:
    """Создаёт разборщик параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="shell_emulator",
        description="Эмулятор языка оболочки UNIX-подобной ОС.",
    )
    parser.add_argument(
        "--vfs",
        metavar="PATH",
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script",
        metavar="PATH",
        help="путь к стартовому скрипту",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Разбирает параметры; при ошибке argparse завершает работу с кодом 2."""
    return build_parser().parse_args(argv)


def format_debug(params: argparse.Namespace) -> list[str]:
    """Возвращает строки отладочного вывода со всеми параметрами запуска."""
    values = vars(params)
    width = max(len(name) for name in values)
    lines = [f"{DEBUG_PREFIX} startup parameters:"]
    for name, value in values.items():
        shown = NOT_SET if value is None else value
        lines.append(f"{DEBUG_PREFIX}   {name:<{width}} = {shown}")
    return lines


def configure_streams() -> None:
    """Включает построчную буферизацию, чтобы вывод не менял порядок."""
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(line_buffering=True)


def enable_line_editing() -> None:
    """Включает редактирование строки и историю стрелками, если возможно."""
    try:
        importlib.import_module("readline")
    except ImportError:
        pass


def main(argv: Sequence[str] | None = None) -> int:
    """Запускает эмулятор с параметрами командной строки.

    Сначала выводятся все параметры, затем выполняется стартовый скрипт
    (если задан), после чего начинается диалог с пользователем.
    Возвращает код завершения процесса.
    """
    params = parse_args(argv)
    configure_streams()
    print("\n".join(format_debug(params)))
    enable_line_editing()
    shell = Shell()
    if params.script is not None:
        try:
            run_script(shell, params.script)
        except ShellError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return EXIT_FAILURE
    return shell.run()
