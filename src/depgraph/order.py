"""Порядок загрузки зависимостей: сначала то, что нужно другим."""

from typing import List

from depgraph.graph import Graph


def load_order(graph: Graph, root: str) -> List[str]:
    """Возвращает пакеты в порядке загрузки: зависимости раньше зависимых.

    Это обратный порядок завершения обхода в глубину (post-order) от
    пакета root, обход идёт без рекурсии. Зависимости пакета посещаются
    в том порядке, в котором они записаны в индексе. Само root — последнее.

    Циклические зависимости упорядочить невозможно: ребро на пакет,
    который уже посещён (в том числе лежит на текущем пути), пропускается,
    поэтому внутри цикла порядок определяется порядком обхода.
    """
    order: List[str] = []
    visited = {root}
    stack = [(root, iter(graph[root]))]
    while stack:
        name, pending = stack[-1]
        for dep in pending:
            if dep not in visited:
                visited.add(dep)
                stack.append((dep, iter(graph[dep])))
                break
        else:
            order.append(name)
            stack.pop()
    return order
