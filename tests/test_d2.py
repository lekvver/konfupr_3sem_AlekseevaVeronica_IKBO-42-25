"""Тесты генерации текста на языке D2."""

import unittest

from depgraph.d2 import CYCLE_STROKE, ROOT_FILL, quote, to_d2
from depgraph.graph import build_graph
from depgraph.testrepo import parse_test_repo


def d2_of(text: str, root: str = "A") -> str:
    """Текст D2 для тестового репозитория из текста."""
    return to_d2(build_graph(root, parse_test_repo(text)), root)


class QuoteTest(unittest.TestCase):
    """Оформление имён."""

    def test_plain_name(self):
        """Имя берётся в кавычки."""
        self.assertEqual(quote("bash"), '"bash"')

    def test_dots_and_pluses_stay_inside_quotes(self):
        """Точки и плюсы остаются внутри строки."""
        self.assertEqual(quote("libstdc++6"), '"libstdc++6"')
        self.assertEqual(quote("python3.12"), '"python3.12"')

    def test_escaping(self):
        """Кавычка и обратная косая черта экранируются."""
        self.assertEqual(quote('a"b\\c'), '"a\\"b\\\\c"')


class ToD2Test(unittest.TestCase):
    """Текст диаграммы."""

    def test_edges_follow_dependencies(self):
        """Ребро идёт от зависимого пакета к его зависимости."""
        text = d2_of("A: B\nB:\n")
        self.assertIn('"A" -> "B"\n', text)
        self.assertNotIn('"B" -> "A"', text)

    def test_root_is_highlighted(self):
        """Анализируемый пакет закрашен."""
        text = d2_of("A: B\nB:\n")
        self.assertIn(f'"A": {{style.fill: "{ROOT_FILL}"}}', text)

    def test_single_package(self):
        """Пакет без зависимостей остаётся на диаграмме."""
        text = d2_of("A:\n")
        self.assertIn('"A": {style.fill:', text)
        self.assertNotIn("->", text)

    def test_cycle_edges_are_red(self):
        """Рёбра цикла красные, остальные — нет."""
        text = d2_of("A: B C\nB: A\nC:\n")
        self.assertIn(f'"A" -> "B": {{style.stroke: "{CYCLE_STROKE}"}}', text)
        self.assertIn(f'"B" -> "A": {{style.stroke: "{CYCLE_STROKE}"}}', text)
        self.assertIn('"A" -> "C"\n', text)

    def test_self_loop_is_red(self):
        """Зависимость от самого себя — красная петля."""
        text = d2_of("A: A\n")
        self.assertIn(f'"A" -> "A": {{style.stroke: "{CYCLE_STROKE}"}}', text)

    def test_ends_with_newline_and_has_direction(self):
        """Текст начинается с направления и заканчивается переводом строки."""
        text = d2_of("A: B\nB:\n")
        self.assertTrue(text.startswith("direction: right\n"))
        self.assertTrue(text.endswith("\n"))

    def test_shared_dependency_has_two_edges(self):
        """Ромб: у D два входящих ребра, сам D описан один раз."""
        text = d2_of("A: B C\nB: D\nC: D\nD:\n")
        self.assertEqual(text.count('-> "D"'), 2)
