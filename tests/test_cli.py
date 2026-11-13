"""Тесты точки входа: вывод параметров и коды возврата."""

import unittest

from depgraph.cli import EXIT_OK, EXIT_USAGE
from helpers import run_main

URL = "http://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/"


class MainTest(unittest.TestCase):
    """Запуск main с разными параметрами."""

    def test_prints_all_params(self):
        """При запуске выводятся все параметры в формате ключ = значение."""
        code, out, err = run_main(["-p", "bash", "-r", URL, "-o", "g.svg"])
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(err, "")
        self.assertIn("package   = bash", out)
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
