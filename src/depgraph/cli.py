"""Точка входа: разбор параметров и запуск этапов работы."""

import sys
from typing import List, Optional, Sequence

from depgraph.apt import load_repository
from depgraph.config import Config, parse_config
from depgraph.errors import ConfigError, DepGraphError, PackageNotFoundError
from depgraph.graph import Graph, build_graph, count_edges, find_cycles
from depgraph.order import load_order
from depgraph.repository import Repository
from depgraph.testrepo import load_test_repo

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
    repo: Repository, chosen: str, group: Sequence[str]
) -> str:
    """Строка о прямой зависимости: выбранный пакет и пометки."""
    notes = []
    if len(group) > 1:
        notes.append("one of: " + " | ".join(group))
    if not repo.is_known(chosen):
        notes.append("not in this index")
    suffix = f" ({'; '.join(notes)})" if notes else ""
    return f"  {chosen}{suffix}"


def direct_dependencies_report(repo: Repository, name: str) -> List[str]:
    """Строки отчёта о прямых зависимостях пакета."""
    pairs = repo.dependency_groups(name)
    title = " ".join(filter(None, [name, repo.version(name)]))
    lines = [f"Direct dependencies of {title} ({len(pairs)}):"]
    lines.extend(describe_dependency(repo, ch, grp) for ch, grp in pairs)
    if not pairs:
        lines.append("  (none)")
    return lines


def graph_report(graph: Graph, root: str) -> List[str]:
    """Строки отчёта о графе зависимостей и найденных циклах."""
    lines = [
        f"Dependency graph of {root}: {len(graph)} packages, "
        f"{count_edges(graph)} edges"
    ]
    for name, deps in graph.items():
        lines.append(f"  {name}: {', '.join(deps) if deps else '(none)'}")
    cycles = find_cycles(graph, root)
    if not cycles:
        lines.append("No cyclic dependencies found")
        return lines
    lines.append(f"Cyclic dependencies found ({len(cycles)}):")
    lines.extend("  " + " -> ".join(cycle) for cycle in cycles)
    return lines


def load_order_report(graph: Graph, root: str) -> List[str]:
    """Строки отчёта о порядке загрузки пакетов (зависимости первыми)."""
    order = load_order(graph, root)
    lines = [
        f"Load order for {root}: {len(order)} packages, "
        "dependencies first"
    ]
    lines.extend(f"  {number}. {name}" for number, name in enumerate(order, 1))
    cycles = find_cycles(graph, root)
    if cycles:
        lines.append(f"Order inside cycles is arbitrary ({len(cycles)} found):")
        lines.extend("  " + " -> ".join(cycle) for cycle in cycles)
    return lines


def load_repo(config: Config) -> Repository:
    """Загружает репозиторий и проверяет, что в нём есть пакет."""
    if config.test_mode:
        repo: Repository = load_test_repo(config.repo)
    else:
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
    if config.direct:
        lines = direct_dependencies_report(repo, config.package)
    else:
        graph = build_graph(config.package, repo)
        if config.load_order:
            lines = load_order_report(graph, config.package)
        else:
            lines = graph_report(graph, config.package)
    print("\n".join(lines))
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
