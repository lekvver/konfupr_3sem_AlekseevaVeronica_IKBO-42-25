"""Тесты построения изображения: запуск d2 и вывод результата."""

import os
import shutil
import stat
import tempfile
import unittest
from unittest import mock

from depgraph.cli import EXIT_FAILURE, EXIT_OK, EXIT_USAGE
from depgraph.render import D2_ENV
from helpers import DATA_DIR, run_main

REPO_FILE = os.path.join(os.path.dirname(DATA_DIR), "repos", "cycle.txt")


def fake_d2(folder: str, body: str) -> str:
    """Создаёт в folder программу-заглушку вместо d2."""
    path = os.path.join(folder, "fake-d2")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("#!/bin/sh\n" + body + "\n")
    os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR)
    return path


class DrawGraphTest(unittest.TestCase):
    """Запись D2 и вызов программы d2."""

    def setUp(self):
        """Создаёт временный каталог для результатов."""
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)
        self.svg = os.path.join(self.folder, "graph.svg")
        self.argv = ["-p", "A", "-r", REPO_FILE, "-t", "-o", self.svg]

    def run_with(self, command: str):
        """Запускает main, подменив программу d2."""
        with mock.patch.dict(os.environ, {D2_ENV: command}):
            return run_main(self.argv)

    def test_d2_text_and_svg_are_created(self):
        """Создаются файл .d2 и изображение, выводятся их имена."""
        command = fake_d2(self.folder, 'cp "$1" "$2"')
        code, out, _ = self.run_with(command)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("graph.d2", out)
        self.assertIn(f"SVG image saved to {self.svg}", out)
        self.assertIn("3 packages, 3 edges, 3 of them in cycles", out)
        self.assertTrue(os.path.isfile(self.svg))
        with open(os.path.join(self.folder, "graph.d2"),
                  encoding="utf-8") as handle:
            self.assertIn('"A" -> "B"', handle.read())

    def test_d2_not_installed(self):
        """Нет программы d2: ошибка с подсказкой, текст D2 сохранён."""
        code, _, err = self.run_with("/no/such/d2")
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("not found; install D2", err)
        self.assertTrue(os.path.isfile(os.path.join(self.folder, "graph.d2")))
        self.assertFalse(os.path.exists(self.svg))

    def test_d2_fails(self):
        """d2 завершился с ошибкой: её текст попадает в сообщение."""
        command = fake_d2(self.folder, 'echo "bad syntax" >&2; exit 3')
        code, _, err = self.run_with(command)
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("d2 failed: bad syntax", err)

    def test_options_are_exclusive(self):
        """--print-graph нельзя сочетать с --direct."""
        code, _, err = run_main(self.argv + ["--direct", "--print-graph"])
        self.assertEqual(code, EXIT_USAGE)
        self.assertIn("mutually exclusive", err)

    @unittest.skipUnless(shutil.which("d2"), "d2 is not installed")
    def test_real_d2(self):
        """С настоящим d2 получается SVG-файл."""
        code, _, _ = run_main(self.argv)
        self.assertEqual(code, EXIT_OK)
        with open(self.svg, encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("<svg", text)
        for name in ("A", "B", "C"):
            self.assertIn(f">{name}<", text)
