"""Текстовое представление графа на языке диаграмм D2 (d2lang.com)."""

from typing import Set, Tuple

from depgraph.graph import Graph, find_cycles

ROOT_FILL = "#fde68a"
CYCLE_STROKE = "#d62728"
DIRECTION = "right"


def quote(name: str) -> str:
    """Оформляет имя как строку D2: в кавычках, с экранированием.

    Кавычки нужны, потому что имена пакетов содержат точки и плюсы
    (python3.12, libstdc++6), а точка в D2 означает вложенность.
    """
    escaped = name.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def cycle_edges(graph: Graph, root: str) -> Set[Tuple[str, str]]:
    """Рёбра, которые входят в найденные циклы."""
    edges: Set[Tuple[str, str]] = set()
    for cycle in find_cycles(graph, root):
        edges.update(zip(cycle, cycle[1:]))
    return edges


def to_d2(graph: Graph, root: str) -> str:
    """Строит текст диаграммы D2 для графа зависимостей.

    Анализируемый пакет закрашен, рёбра внутри циклов — красные.
    Ребро «A -> B» означает: пакет A зависит от пакета B.
    """
    in_cycle = cycle_edges(graph, root)
    lines = [
        f"direction: {DIRECTION}",
        "",
        f'{quote(root)}: {{style.fill: "{ROOT_FILL}"}}',
    ]
    for name, deps in graph.items():
        for dep in deps:
            line = f"{quote(name)} -> {quote(dep)}"
            if (name, dep) in in_cycle:
                line += f': {{style.stroke: "{CYCLE_STROKE}"}}'
            lines.append(line)
    return "\n".join(lines) + "\n"
