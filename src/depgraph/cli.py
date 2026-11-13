"""Точка входа: разбор параметров и запуск этапов работы."""

import sys
from typing import List, Optional, Sequence

from depgraph.config import Config, parse_config
from depgraph.errors import ConfigError, DepGraphError

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
HELP_HINT = "try: depgraph --help"


def format_params(config: Config) -> List[str]:
    """Форматирует параметры строками вида «ключ = значение»."""
    pairs = config.as_pairs()
    width = max(len(key) for key, _ in pairs)
    return [f"{key.ljust(width)} = {value}" for key, value in pairs]


def run(argv: Optional[Sequence[str]]) -> int:
    """Выполняет работу программы; ошибки передаёт вызывающему."""
    config = parse_config(argv)
    for line in format_params(config):
        print(line)
    return EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Запускает программу и превращает ошибки в код возврата."""
    try:
        return run(argv)
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        print(HELP_HINT, file=sys.stderr)
        return EXIT_USAGE
    except DepGraphError as error:
        print(f"error: {error}", file=sys.stderr)
        return EXIT_FAILURE
