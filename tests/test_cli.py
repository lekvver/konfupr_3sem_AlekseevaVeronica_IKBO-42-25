"""Тесты параметров командной строки и главной функции."""

import contextlib
import io
import os
import tempfile
import unittest

from shell_emulator.cli import format_debug, main, parse_args


def run_main(argv):
    """Вызывает main с перехватом вывода; возвращает код, stdout, stderr."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class ParseArgsTest(unittest.TestCase):
    """Разбор параметров командной строки."""

    def test_defaults(self):
        """Без параметров оба значения не заданы."""
        params = parse_args([])
        self.assertIsNone(params.vfs)
        self.assertIsNone(params.script)

    def test_both_parameters(self):
        """Заданные параметры попадают в результат."""
        params = parse_args(["--vfs", "/data/vfs", "--script", "s.emu"])
        self.assertEqual(params.vfs, "/data/vfs")
        self.assertEqual(params.script, "s.emu")

    def test_unknown_option_exits_with_2(self):
        """Неизвестный параметр: argparse завершает работу с кодом 2."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                parse_args(["--bogus"])
        self.assertEqual(ctx.exception.code, 2)

    def test_missing_value_exits_with_2(self):
        """Параметр без значения тоже считается ошибкой."""
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                parse_args(["--vfs"])
        self.assertEqual(ctx.exception.code, 2)


class FormatDebugTest(unittest.TestCase):
    """Отладочный вывод параметров."""

    def test_not_set(self):
        """Незаданные параметры выводятся как <not set>."""
        lines = format_debug(parse_args([]))
        self.assertEqual(lines[1], "[debug]   vfs    = <not set>")
        self.assertEqual(lines[2], "[debug]   script = <not set>")

    def test_values(self):
        """Заданные параметры выводятся со своими значениями."""
        lines = format_debug(parse_args(["--vfs", "a", "--script", "b"]))
        self.assertEqual(lines[1], "[debug]   vfs    = a")
        self.assertEqual(lines[2], "[debug]   script = b")


class MainTest(unittest.TestCase):
    """Запуск эмулятора целиком."""

    def setUp(self):
        """Создаёт временный каталог для скриптов."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def script(self, text):
        """Записывает скрипт и возвращает его путь."""
        path = os.path.join(self.tmp.name, "start.emu")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
        return path

    def test_debug_output_comes_first(self):
        """Параметры выводятся до выполнения скрипта."""
        path = self.script("exit\n")
        code, out, _ = run_main(["--script", path])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("[debug] startup parameters:\n"))
        self.assertIn(f"[debug]   script = {path}\n", out)

    def test_script_exit_code_is_returned(self):
        """Код exit из скрипта становится кодом завершения эмулятора."""
        code, out, _ = run_main(["--script", self.script("ls x\nexit 6\n")])
        self.assertEqual(code, 6)
        self.assertIn("ls: args=['x']", out)

    def test_missing_script(self):
        """Отсутствующий скрипт: сообщение об ошибке и код 1."""
        path = os.path.join(self.tmp.name, "nope.emu")
        code, _, err = run_main(["--script", path])
        self.assertEqual(code, 1)
        self.assertIn("cannot read startup script", err)


class MainVfsTest(unittest.TestCase):
    """Загрузка VFS при запуске эмулятора."""

    def setUp(self):
        """Создаёт временный каталог и каталог-источник VFS."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.vfs_dir = os.path.join(self.tmp.name, "vfs")
        os.makedirs(os.path.join(self.vfs_dir, "dir"))
        with open(os.path.join(self.vfs_dir, "f.txt"), "w") as stream:
            stream.write("data")

    def script(self, text):
        """Записывает стартовый скрипт и возвращает его путь."""
        path = os.path.join(self.tmp.name, "start.emu")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
        return path

    def test_vfs_is_loaded(self):
        """Сообщение о загрузке содержит путь и число элементов."""
        script = self.script("exit\n")
        code, out, _ = run_main(["--vfs", self.vfs_dir, "--script", script])
        self.assertEqual(code, 0)
        expected = f"[info] VFS loaded from {self.vfs_dir}: "
        self.assertIn(expected + "1 directories, 1 files", out)

    def test_default_vfs(self):
        """Без --vfs создаётся VFS по умолчанию."""
        code, out, _ = run_main(["--script", self.script("exit\n")])
        self.assertEqual(code, 0)
        self.assertIn("no VFS path given, default in-memory VFS", out)

    def test_missing_vfs(self):
        """Нет каталога VFS: сообщение об ошибке, код 1, скрипт не запущен."""
        missing = os.path.join(self.tmp.name, "nope")
        script = self.script("ls should-not-run\nexit\n")
        code, out, err = run_main(["--vfs", missing, "--script", script])
        self.assertEqual(code, 1)
        self.assertIn("error: VFS not found", err)
        self.assertNotIn("should-not-run", out)

    def test_vfs_is_not_a_directory(self):
        """Файл вместо каталога: ошибка неверного формата, код 1."""
        path = os.path.join(self.vfs_dir, "f.txt")
        code, _, err = run_main(["--vfs", path])
        self.assertEqual(code, 1)
        self.assertIn("error: invalid VFS format", err)

    def test_vfs_save_from_script(self):
        """vfs-save из скрипта сохраняет загруженную VFS."""
        out_dir = os.path.join(self.tmp.name, "saved")
        script = self.script(f'vfs-save "{out_dir}"\nexit\n')
        code, _, _ = run_main(["--vfs", self.vfs_dir, "--script", script])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "f.txt")))
        self.assertTrue(os.path.isdir(os.path.join(out_dir, "dir")))


if __name__ == "__main__":
    unittest.main()
