"""Точка входа: разбор параметров и запуск этапов работы."""

import sys
from typing import List, Optional, Sequence

from depgraph.apt import AptRepository, load_repository
from depgraph.config import Config, parse_config
from depgraph.errors import (
    ConfigError,
    DepGraphError,
    PackageNotFoundError,
    RepositoryError,
)

EXIT_OK = 0
EXIT_FAILURE = 1
EXIT_USAGE = 2
HELP_HINT = "try: depgraph --help"


def format_params(config: Config) -> List[str]:
    """Форматирует параметры строками вида «ключ = значение»."""
    pairs = config.as_pairs()
    width = max(len(key) for key, _ in pairs)
    return [f"{key.ljust(width)} = {value}" for key, value in pairs]


def describe_dependency(
    repo: AptRepository, chosen: str, group: Sequence[str]
) -> str:
    """Строка о прямой зависимости: выбранный пакет и пометки."""
    notes = []
    if len(group) > 1:
        notes.append("one of: " + " | ".join(group))
    if not repo.is_known(chosen):
        notes.append("not in this index")
    suffix = f" ({'; '.join(notes)})" if notes else ""
    return f"  {chosen}{suffix}"


def direct_dependencies_report(repo: AptRepository, name: str) -> List[str]:
    """Строки отчёта о прямых зависимостях пакета."""
    pairs = repo.dependency_groups(name)
    head = f"Direct dependencies of {name} {repo.version(name)} ({len(pairs)}):"
    lines = [head]
    lines.extend(describe_dependency(repo, ch, grp) for ch, grp in pairs)
    if not pairs:
        lines.append("  (none)")
    return lines


def load_repo(config: Config) -> AptRepository:
    """Загружает репозиторий и проверяет, что в нём есть пакет."""
    if config.test_mode:
        raise RepositoryError("test mode is not supported yet")
    repo = load_repository(config.repo)
    if not repo.has_package(config.package):
        raise PackageNotFoundError(
            f"package {config.package!r} not found in repository"
        )
    return repo


def run(argv: Optional[Sequence[str]]) -> int:
    """Выполняет работу программы; ошибки передаёт вызывающему."""
    config = parse_config(argv)
    if config.print_params:
        print("\n".join(format_params(config)))
    repo = load_repo(config)
    print("\n".join(direct_dependencies_report(repo, config.package)))
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
