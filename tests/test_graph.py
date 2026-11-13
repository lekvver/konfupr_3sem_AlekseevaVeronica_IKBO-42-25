"""Тесты построения графа (BFS с рекурсией) и поиска циклов."""

import unittest

from depgraph.errors import GraphError
from depgraph.graph import build_graph, count_edges, find_cycles
from depgraph.testrepo import parse_test_repo


def graph_of(text: str, root: str = "A"):
    """Строит граф для тестового репозитория из текста."""
    return build_graph(root, parse_test_repo(text))


class BuildGraphTest(unittest.TestCase):
    """Построение графа."""

    def test_single_package(self):
        """Пакет без зависимостей: граф из одной вершины."""
        self.assertEqual(graph_of("A:\n"), {"A": []})

    def test_linear_chain(self):
        """Цепочка учитывает транзитивные зависимости."""
        graph = graph_of("A: B\nB: C\nC:\n")
        self.assertEqual(graph, {"A": ["B"], "B": ["C"], "C": []})

    def test_bfs_order(self):
        """Вершины идут по уровням: сначала все соседи, потом их соседи."""
        graph = graph_of("A: B C\nB: D\nC: E\nD:\nE:\n")
        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])

    def test_shortest_level_first(self):
        """Пакет попадает на тот уровень, где он встретился впервые."""
        graph = graph_of("A: B C\nB: D\nC: D\nD: E\nE:\n")
        self.assertEqual(list(graph), ["A", "B", "C", "D", "E"])

    def test_diamond_visits_shared_once(self):
        """Общая зависимость в графе одна."""
        graph = graph_of("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(len(graph), 4)
        self.assertEqual(count_edges(graph), 4)

    def test_unreachable_packages_are_skipped(self):
        """Недостижимые от корня пакеты в граф не входят."""
        graph = graph_of("A: B\nB:\nX: Y\nY:\n")
        self.assertEqual(set(graph), {"A", "B"})

    def test_cycle_terminates(self):
        """Цикл не приводит к бесконечному обходу."""
        graph = graph_of("A: B\nB: C\nC: A\n")
        self.assertEqual(set(graph), {"A", "B", "C"})

    def test_self_loop(self):
        """Зависимость пакета от самого себя."""
        graph = graph_of("A: A B\nB:\n")
        self.assertEqual(graph["A"], ["A", "B"])

    def test_root_other_than_first(self):
        """Корнем может быть любой пакет репозитория."""
        graph = graph_of("A: B\nB: C\nC:\n", root="B")
        self.assertEqual(list(graph), ["B", "C"])

    def test_too_deep_chain(self):
        """Слишком длинная цепочка даёт GraphError, а не RecursionError."""
        size = 3000
        names = ["N%d" % i for i in range(size)]
        graph = {name: [nxt] for name, nxt in zip(names, names[1:])}
        graph[names[-1]] = []

        class Chain:
            """Репозиторий-цепочка."""

            @staticmethod
            def dependencies(name):
                """Зависимость от следующего звена."""
                return graph[name]

        with self.assertRaisesRegex(GraphError, "too deep"):
            build_graph(names[0], Chain())


class FindCyclesTest(unittest.TestCase):
    """Поиск циклических зависимостей."""

    def test_acyclic(self):
        """В ромбе циклов нет."""
        graph = graph_of("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(find_cycles(graph, "A"), [])

    def test_simple_cycle(self):
        """Простой цикл записывается путём с повтором первой вершины."""
        graph = graph_of("A: B\nB: C\nC: A\n")
        self.assertEqual(find_cycles(graph, "A"), [["A", "B", "C", "A"]])

    def test_self_loop_is_cycle(self):
        """Зависимость от самого себя — цикл."""
        graph = graph_of("A: A\n")
        self.assertEqual(find_cycles(graph, "A"), [["A", "A"]])

    def test_two_cycles(self):
        """Два цикла находятся оба."""
        graph = graph_of("A: B C\nB: A D\nC: D\nD: B\n")
        self.assertEqual(
            find_cycles(graph, "A"),
            [["A", "B", "A"], ["B", "D", "B"]],
        )

    def test_cycle_not_through_root(self):
        """Цикл, до которого путь идёт через несколько пакетов."""
        graph = graph_of("A: B\nB: C\nC: D\nD: B\n")
        self.assertEqual(find_cycles(graph, "A"), [["B", "C", "D", "B"]])
