"""Точка входа: параметры командной строки и запуск эмулятора."""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Sequence

from .errors import ShellError
from .script import run_script
from .shell import Shell
from .vfs import Vfs

EXIT_FAILURE = 1
NOT_SET = "<not set>"
DEBUG_PREFIX = "[debug]"
INFO_PREFIX = "[info]"


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


def load_vfs(path: str | None) -> Vfs:
    """Загружает VFS из каталога path или создаёт VFS по умолчанию."""
    if path is None:
        return Vfs.default()
    return Vfs.from_directory(path)


def describe_vfs(vfs: Vfs, path: str | None) -> str:
    """Возвращает строку: откуда получена VFS и сколько в ней элементов."""
    dirs, files = vfs.count()
    stats = f"{dirs} directories, {files} files"
    if path is None:
        return (
            f"{INFO_PREFIX} no VFS path given, "
            f"default in-memory VFS created: {stats}"
        )
    return f"{INFO_PREFIX} VFS loaded from {path}: {stats}"


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

    Сначала выводятся все параметры, затем загружается VFS (или создаётся
    VFS по умолчанию), выполняется стартовый скрипт (если задан), после
    чего начинается диалог с пользователем. Ошибка загрузки VFS или чтения
    скрипта завершает работу с кодом 1. Возвращает код завершения.
    """
    params = parse_args(argv)
    configure_streams()
    print("\n".join(format_debug(params)))
    try:
        vfs = load_vfs(params.vfs)
        print(describe_vfs(vfs, params.vfs))
        enable_line_editing()
        shell = Shell(vfs=vfs)
        if params.script is not None:
            run_script(shell, params.script)
    except ShellError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_FAILURE
    return shell.run()
