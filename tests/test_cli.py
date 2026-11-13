"""Тесты точки входа: вывод параметров и коды возврата."""

import unittest

from depgraph.cli import EXIT_FAILURE, EXIT_OK, EXIT_USAGE
from helpers import INDEX_URL, run_main

URL = INDEX_URL


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
        code, out, _ = run_main(["-p", "app", "-r", self.index_url])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Direct dependencies of app 1.0-1 (5):", out)
        self.assertIn("  base\n", out)
        self.assertIn("  libbaz (one of: libbar | libbaz)", out)
        self.assertIn("  mta-one\n", out)
        self.assertIn("  missing-pkg (not in this index)", out)

    def test_package_without_dependencies(self):
        """Пакет без зависимостей: (none)."""
        _, out, _ = run_main(["-p", "base", "-r", self.index_url])
        self.assertIn("(0):", out)
        self.assertIn("(none)", out)

    def test_unknown_package(self):
        """Неизвестный пакет: ошибка и код 1."""
        code, _, err = run_main(["-p", "zzz", "-r", self.index_url])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("package 'zzz' not found", err)

    def test_print_params_option(self):
        """--print-params выводит параметры перед результатом."""
        _, out, _ = run_main(
            ["-p", "base", "-r", self.index_url, "--print-params"])
        self.assertTrue(out.startswith("package   = base"))

    def test_bad_repository(self):
        """Репозиторий без индекса: ошибка и код 1."""
        code, _, err = run_main(["-p", "base", "-r", "file:///no/such/dir"])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("package index not found", err)
