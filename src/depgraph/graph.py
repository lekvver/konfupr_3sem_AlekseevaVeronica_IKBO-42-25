"""Граф зависимостей: построение (BFS с рекурсией) и поиск циклов."""

from typing import Dict, List

from depgraph.errors import GraphError
from depgraph.repository import Repository

Graph = Dict[str, List[str]]

ON_PATH = 1
DONE = 2


def _bfs_level(level: List[str], graph: Graph, repo: Repository) -> None:
    """Обрабатывает один уровень обхода в ширину и вызывает себя для
    следующего уровня.

    Пакеты уровня ещё не входят в graph. Следующий уровень составляют
    зависимости, которых нет ни в graph, ни в самом следующем уровне:
    так каждый пакет обрабатывается один раз, и циклы не зацикливают обход.
    """
    if not level:
        return
    for name in level:
        graph[name] = repo.dependencies(name)
    following: List[str] = []
    for name in level:
        for dep in graph[name]:
            if dep not in graph and dep not in following:
                following.append(dep)
    _bfs_level(following, graph, repo)


def build_graph(root: str, repo: Repository) -> Graph:
    """Строит граф всех (транзитивных) зависимостей пакета root.

    Ключи словаря идут в порядке обхода в ширину, значения — списки
    прямых зависимостей. Рекурсия идёт по уровням, поэтому её глубина
    равна длине самой длинной кратчайшей цепочки от root.
    """
    graph: Graph = {}
    try:
        _bfs_level([root], graph, repo)
    except RecursionError as error:
        raise GraphError("dependency chain is too deep") from error
    return graph


def find_cycles(graph: Graph, root: str) -> List[List[str]]:
    """Находит циклы обходом в глубину (без рекурсии).

    Каждое обратное ребро (на пакет, который лежит на текущем пути)
    даёт цикл, записанный как путь: [A, B, C, A].
    """
    cycles: List[List[str]] = []
    state = {root: ON_PATH}
    path = [root]
    stack = [iter(graph[root])]
    while stack:
        descended = False
        for dep in stack[-1]:
            if dep not in state:
                state[dep] = ON_PATH
                path.append(dep)
                stack.append(iter(graph[dep]))
                descended = True
                break
            if state[dep] == ON_PATH:
                cycles.append(path[path.index(dep):] + [dep])
        if not descended:
            state[path.pop()] = DONE
            stack.pop()
    return cycles


def count_edges(graph: Graph) -> int:
    """Число рёбер (зависимостей) в графе."""
    return sum(len(deps) for deps in graph.values())
