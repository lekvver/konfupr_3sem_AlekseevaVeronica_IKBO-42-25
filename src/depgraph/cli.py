"""Точка входа: разбор параметров и запуск этапов работы."""

import os
import sys
from typing import List, Optional, Sequence

from depgraph.apt import load_repository
from depgraph.config import Config, parse_config
from depgraph.d2 import cycle_edges, to_d2
from depgraph.errors import (
    ConfigError,
    DepGraphError,
    PackageNotFoundError,
    RenderError,
)
from depgraph.graph import Graph, build_graph, count_edges, find_cycles
from depgraph.order import load_order
from depgraph.render import render_svg
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


def d2_path_for(svg_path: str) -> str:
    """Путь к файлу с текстом D2: рядом с изображением, расширение .d2."""
    return os.path.splitext(svg_path)[0] + ".d2"


def write_text(path: str, text: str) -> None:
    """Записывает текстовый файл в UTF-8."""
    try:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
    except OSError as error:
        raise RenderError(f"cannot write {path}: {error}") from error


def draw_graph(config: Config, graph: Graph) -> int:
    """Записывает текст D2 и строит по нему SVG-изображение."""
    d2_path = d2_path_for(config.output)
    write_text(d2_path, to_d2(graph, config.package))
    print(f"D2 text saved to {d2_path}")
    render_svg(d2_path, config.output)
    print(f"SVG image saved to {config.output}")
    cyclic = len(cycle_edges(graph, config.package))
    print(
        f"{len(graph)} packages, {count_edges(graph)} edges, "
        f"{cyclic} of them in cycles (red)"
    )
    return EXIT_OK


def show(lines: List[str]) -> int:
    """Печатает строки отчёта."""
    print("\n".join(lines))
    return EXIT_OK


def run(argv: Optional[Sequence[str]]) -> int:
    """Выполняет работу программы; ошибки передаёт вызывающему."""
    config = parse_config(argv)
    if config.print_params:
        print("\n".join(format_params(config)))
    repo = load_repo(config)
    if config.direct:
        return show(direct_dependencies_report(repo, config.package))
    graph = build_graph(config.package, repo)
    if config.load_order:
        return show(load_order_report(graph, config.package))
    if config.print_graph:
        return show(graph_report(graph, config.package))
    return draw_graph(config, graph)


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
