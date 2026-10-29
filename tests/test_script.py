"""Тесты стартового скрипта."""

import os
import tempfile
import unittest

from helpers import TEST_PROMPT, make_shell
from shell_emulator.errors import ShellError
from shell_emulator.script import read_script, run_script


class ScriptTestCase(unittest.TestCase):
    """Базовый класс: создаёт временный каталог для файлов скриптов."""

    def setUp(self):
        """Создаёт временный каталог перед каждым тестом."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write_script(self, text, name="start.emu", encoding="utf-8"):
        """Записывает скрипт во временный каталог и возвращает путь."""
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding=encoding, newline="") as stream:
            stream.write(text)
        return path

    def run_text(self, text, env=None):
        """Выполняет скрипт с текстом text; возвращает оболочку и путь."""
        path = self.write_script(text)
        shell = make_shell(env=env)
        run_script(shell, path)
        return shell, path


class RunScriptTest(ScriptTestCase):
    """Выполнение корректных скриптов."""

    def test_input_and_output_are_shown(self):
        """На экране видны и введённая команда, и её вывод."""
        shell, _ = self.run_text("ls -l\n")
        expected = f"{TEST_PROMPT}ls -l\nls: args=['-l']\n"
        self.assertEqual(shell.out.getvalue(), expected)

    def test_commands_run_in_order(self):
        """Команды выполняются последовательно."""
        shell, _ = self.run_text("cd a\ncd b\n")
        lines = shell.out.getvalue().splitlines()
        self.assertEqual(lines[1], "cd: args=['a']")
        self.assertEqual(lines[3], "cd: args=['b']")

    def test_environment_variables(self):
        """В скрипте раскрываются переменные окружения."""
        shell, _ = self.run_text("cd $HOME\n", env={"HOME": "/h"})
        self.assertIn("cd: args=['/h']", shell.out.getvalue())

    def test_blank_lines_are_not_shown(self):
        """Пустые строки не выводятся и не выполняются."""
        shell, _ = self.run_text("\n  \nls\n")
        self.assertEqual(shell.out.getvalue().count(TEST_PROMPT), 1)

    def test_comment_is_shown_but_does_nothing(self):
        """Комментарий отображается как ввод, но ничего не делает."""
        shell, _ = self.run_text("# note\n")
        self.assertEqual(shell.out.getvalue(), f"{TEST_PROMPT}# note\n")
        self.assertEqual(shell.err.getvalue(), "")

    def test_exit_stops_script(self):
        """После exit остальные строки не выполняются."""
        shell, _ = self.run_text("exit 4\nls\n")
        self.assertEqual(shell.exit_code, 4)
        self.assertNotIn("ls: args", shell.out.getvalue())

    def test_windows_line_endings_and_bom(self):
        """Скрипт с CRLF и BOM читается правильно."""
        path = self.write_script("\ufeffls a\r\ncd b\r\n")
        self.assertEqual(read_script(path), ["ls a", "cd b"])


class ScriptErrorsTest(ScriptTestCase):
    """Ошибки при выполнении скрипта."""

    def test_unknown_command_is_skipped(self):
        """Неизвестная команда: сообщение с номером строки, дальше работа."""
        shell, path = self.run_text("ls a\nfoo\ncd b\n")
        expected = f"{path}: line 2: foo: command not found\n"
        self.assertEqual(shell.err.getvalue(), expected)
        self.assertIn("cd: args=['b']", shell.out.getvalue())

    def test_parse_error_is_skipped(self):
        """Ошибка разбора пропускает только свою строку."""
        shell, path = self.run_text("ls 'oops\ncd b\n")
        self.assertIn(f"{path}: line 1: syntax error", shell.err.getvalue())
        self.assertIn("cd: args=['b']", shell.out.getvalue())

    def test_bad_line_is_still_shown(self):
        """Ошибочная строка тоже выводится как ввод пользователя."""
        shell, _ = self.run_text("foo\n")
        self.assertIn(f"{TEST_PROMPT}foo", shell.out.getvalue())

    def test_missing_file(self):
        """Отсутствующий файл скрипта — ошибка с указанием причины."""
        path = os.path.join(self.tmp.name, "missing.emu")
        with self.assertRaises(ShellError) as ctx:
            run_script(make_shell(), path)
        self.assertIn("cannot read startup script", str(ctx.exception))
        self.assertIn("No such file", str(ctx.exception))

    def test_directory_instead_of_file(self):
        """Каталог вместо файла скрипта — тоже ошибка чтения."""
        with self.assertRaises(ShellError):
            read_script(self.tmp.name)

    def test_not_a_text_file(self):
        """Файл не в кодировке UTF-8 сообщает об ошибке."""
        path = os.path.join(self.tmp.name, "bad.emu")
        with open(path, "wb") as stream:
            stream.write(b"\xff\xfe\xfa\n")
        with self.assertRaises(ShellError) as ctx:
            read_script(path)
        self.assertIn("not a UTF-8 text file", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
