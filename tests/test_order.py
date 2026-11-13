"""Тесты порядка загрузки зависимостей."""

import unittest

from depgraph.graph import build_graph, find_cycles
from depgraph.order import load_order
from depgraph.testrepo import parse_test_repo


def order_of(text: str, root: str = "A"):
    """Порядок загрузки для тестового репозитория из текста."""
    graph = build_graph(root, parse_test_repo(text))
    return load_order(graph, root)


class LoadOrderTest(unittest.TestCase):
    """Порядок загрузки: зависимости раньше зависимых."""

    def test_single_package(self):
        """Пакет без зависимостей загружается один."""
        self.assertEqual(order_of("A:\n"), ["A"])

    def test_chain(self):
        """Цепочка загружается с конца."""
        self.assertEqual(order_of("A: B\nB: C\nC:\n"), ["C", "B", "A"])

    def test_diamond(self):
        """Общая зависимость загружается один раз и до обоих зависимых."""
        self.assertEqual(
            order_of("A: B C\nB: D\nC: D\nD:\n"), ["D", "B", "C", "A"])

    def test_tree_follows_record_order(self):
        """Зависимости посещаются в порядке записи."""
        text = "A: B C\nB: D E\nC: F\nD:\nE:\nF:\n"
        self.assertEqual(order_of(text), ["D", "E", "B", "F", "C", "A"])

    def test_root_is_last(self):
        """Анализируемый пакет всегда загружается последним."""
        self.assertEqual(order_of("A: C B\nB: C\nC:\n")[-1], "A")

    def test_cycle_is_broken(self):
        """Цикл не мешает: обратное ребро пропускается."""
        self.assertEqual(order_of("A: B\nB: C\nC: A\n"), ["C", "B", "A"])

    def test_self_loop(self):
        """Зависимость от самого себя игнорируется."""
        self.assertEqual(order_of("A: A B\nB:\n"), ["B", "A"])

    def test_each_package_once(self):
        """Каждый пакет графа встречается ровно один раз."""
        text = "A: B C\nB: D\nC: D E\nD: F\nE: F\nF: B\n"
        order = order_of(text)
        self.assertEqual(sorted(order), ["A", "B", "C", "D", "E", "F"])

    def test_dependencies_precede_dependents(self):
        """Для рёбер вне циклов зависимость стоит раньше зависимого."""
        text = "A: B C\nB: D\nC: D E\nD: F\nE: F\nF: B\nX: A\n"
        graph = build_graph("A", parse_test_repo(text))
        in_cycle = set()
        for cycle in find_cycles(graph, "A"):
            in_cycle.update(zip(cycle, cycle[1:]))
        position = {name: i for i, name in enumerate(load_order(graph, "A"))}
        for name, deps in graph.items():
            for dep in deps:
                if (name, dep) not in in_cycle:
                    self.assertLess(position[dep], position[name])
