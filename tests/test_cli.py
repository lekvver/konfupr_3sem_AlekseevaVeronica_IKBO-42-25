"""Тесты точки входа: вывод параметров и коды возврата."""

import os
import unittest

from depgraph.cli import EXIT_FAILURE, EXIT_OK, EXIT_USAGE
from helpers import DATA_DIR, INDEX_URL, run_main, temp_file

URL = INDEX_URL
REPOS_DIR = os.path.join(os.path.dirname(DATA_DIR), "repos")


class MainTest(unittest.TestCase):
    """Запуск main с разными параметрами."""

    def test_prints_all_params(self):
        """--print-params выводит параметры в формате ключ = значение."""
        _, out, _ = run_main(
            ["-p", "base", "-r", URL, "-o", "g.svg", "--print-params"])
        self.assertIn("package   = base", out)
        self.assertIn(f"repo      = {URL}", out)
        self.assertIn("test_mode = false", out)
        self.assertIn("output    = g.svg", out)

    def test_error_goes_to_stderr(self):
        """Ошибка: сообщение в stderr, код 2, stdout пуст."""
        code, out, err = run_main(["-p", "Bash", "-r", URL])
        self.assertEqual(code, EXIT_USAGE)
        self.assertEqual(out, "")
        self.assertIn("error: invalid package name", err)

    def test_help_exits(self):
        """Справка завершает работу кодом 0."""
        with self.assertRaises(SystemExit) as caught:
            run_main(["--help"])
        self.assertEqual(caught.exception.code, 0)


class DirectDependenciesTest(unittest.TestCase):
    """Вывод прямых зависимостей на этапе 2."""

    index_url = INDEX_URL

    def test_prints_direct_dependencies(self):
        """Выводятся прямые зависимости с пометками."""
        code, out, _ = run_main(["-p", "app", "-r", self.index_url, "--direct"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Direct dependencies of app 1.0-1 (5):", out)
        self.assertIn("  base\n", out)
        self.assertIn("  libbaz (one of: libbar | libbaz)", out)
        self.assertIn("  mta-one\n", out)
        self.assertIn("  missing-pkg (not in this index)", out)

    def test_package_without_dependencies(self):
        """Пакет без зависимостей: (none)."""
        _, out, _ = run_main(["-p", "base", "-r", self.index_url, "--direct"])
        self.assertIn("(0):", out)
        self.assertIn("(none)", out)

    def test_unknown_package(self):
        """Неизвестный пакет: ошибка и код 1."""
        code, _, err = run_main(["-p", "zzz", "-r", self.index_url, "--direct"])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("package 'zzz' not found", err)

    def test_print_params_option(self):
        """--print-params выводит параметры перед результатом."""
        _, out, _ = run_main(
            ["-p", "base", "-r", self.index_url, "--direct", "--print-params"])
        self.assertTrue(out.startswith("package   = base"))

    def test_bad_repository(self):
        """Репозиторий без индекса: ошибка и код 1."""
        code, _, err = run_main(
            ["-p", "base", "-r", "file:///no/such/dir", "--direct"])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("package index not found", err)


class GraphModeTest(unittest.TestCase):
    """Построение графа и тестовый режим (этап 3)."""

    def repo(self, name):
        """Путь к файлу из tests/repos."""
        return os.path.join(REPOS_DIR, name)

    def test_acyclic_graph(self):
        """Граф без циклов: список смежности и сообщение об отсутствии."""
        code, out, _ = run_main(
            ["-p", "A", "-r", self.repo("diamond.txt"), "-t"])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Dependency graph of A: 4 packages, 4 edges", out)
        self.assertIn("  A: B, C\n  B: D\n  C: D\n  D: (none)\n", out)
        self.assertIn("No cyclic dependencies found", out)

    def test_cycle_is_reported(self):
        """Цикл выводится путём."""
        _, out, _ = run_main(["-p", "A", "-r", self.repo("cycle.txt"), "-t"])
        self.assertIn("Cyclic dependencies found (1):", out)
        self.assertIn("  A -> B -> C -> A", out)

    def test_other_root(self):
        """Анализ другого пакета того же файла."""
        _, out, _ = run_main(
            ["-p", "X", "-r", self.repo("complex.txt"), "-t"])
        self.assertIn("Dependency graph of X: 2 packages, 1 edges", out)

    def test_package_not_in_test_repo(self):
        """Пакета нет в тестовом репозитории."""
        code, _, err = run_main(
            ["-p", "Q", "-r", self.repo("linear.txt"), "-t"])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("package 'Q' not found", err)

    def test_broken_test_repo(self):
        """Ошибка в файле: сообщение с номером строки, код 1."""
        with temp_file("A: B\nbroken\n") as path:
            code, _, err = run_main(["-p", "A", "-r", path, "-t"])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("line 2", err)

    def test_direct_option(self):
        """--direct выводит только прямые зависимости."""
        _, out, _ = run_main(
            ["-p", "A", "-r", self.repo("tree.txt"), "-t", "--direct"])
        self.assertEqual(
            out, "Direct dependencies of A (2):\n  B\n  C\n")

    def test_real_mode_graph(self):
        """Граф по индексу apt: виртуальные пакеты и цикл libc6."""
        _, out, _ = run_main(["-p", "libc6", "-r", INDEX_URL])
        self.assertIn("Dependency graph of libc6: 2 packages, 2 edges", out)
        self.assertIn("libc6 -> libgcc-s1 -> libc6", out)


class LoadOrderModeTest(unittest.TestCase):
    """Режим --load-order (этап 4)."""

    def test_order_output(self):
        """Выводится нумерованный список, зависимости первыми."""
        path = os.path.join(REPOS_DIR, "diamond.txt")
        code, out, _ = run_main(["-p", "A", "-r", path, "-t", "--load-order"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(
            out,
            "Load order for A: 4 packages, dependencies first\n"
            "  1. D\n  2. B\n  3. C\n  4. A\n",
        )

    def test_cycles_are_mentioned(self):
        """Если есть циклы, они перечисляются."""
        path = os.path.join(REPOS_DIR, "cycle.txt")
        _, out, _ = run_main(["-p", "A", "-r", path, "-t", "--load-order"])
        self.assertIn("  1. C\n  2. B\n  3. A\n", out)
        self.assertIn("Order inside cycles is arbitrary (1 found):", out)
        self.assertIn("  A -> B -> C -> A", out)

    def test_real_mode_order(self):
        """Порядок по индексу apt: libc6 и libgcc-s1 образуют цикл."""
        _, out, _ = run_main(
            ["-p", "libc6", "-r", INDEX_URL, "--load-order"])
        self.assertIn("  1. libgcc-s1\n  2. libc6\n", out)

    def test_exclusive_with_direct(self):
        """--direct и --load-order вместе не допускаются."""
        code, _, err = run_main(
            ["-p", "base", "-r", INDEX_URL, "--direct", "--load-order"])
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("mutually exclusive", err)
