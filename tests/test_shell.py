"""Тесты ядра эмулятора: приглашение, команды и интерактивный цикл."""

import unittest
from unittest import mock

from helpers import make_shell
from shell_emulator.shell import build_prompt


def run_lines(*lines, env=None):
    """Запускает цикл на заданных строках; возвращает оболочку и код."""
    shell = make_shell(lines, env)
    code = shell.run()
    return shell, code


class PromptTest(unittest.TestCase):
    """Приглашение строится из данных реальной ОС."""

    def test_prompt_format(self):
        """Формат приглашения: пользователь@хост:~$ и пробел."""
        with mock.patch("getpass.getuser", return_value="alice"), \
                mock.patch("socket.gethostname", return_value="box"):
            self.assertEqual(build_prompt(), "alice@box:~$ ")

    def test_prompt_without_user_database(self):
        """Если имя пользователя определить нельзя, берётся user."""
        with mock.patch("getpass.getuser", side_effect=KeyError), \
                mock.patch("socket.gethostname", return_value="box"):
            self.assertEqual(build_prompt(), "user@box:~$ ")


class StubCommandsTest(unittest.TestCase):
    """Команды-заглушки ls и cd выводят имя и аргументы."""

    def test_ls_with_arguments(self):
        """ls показывает свои аргументы списком."""
        shell, _ = run_lines("ls -l /tmp", "exit")
        self.assertEqual(shell.out.getvalue(), "ls: args=['-l', '/tmp']\n")

    def test_ls_without_arguments(self):
        """ls без аргументов показывает пустой список."""
        shell, _ = run_lines("ls", "exit")
        self.assertEqual(shell.out.getvalue(), "ls: args=[]\n")

    def test_cd_with_argument(self):
        """cd показывает свой аргумент."""
        shell, _ = run_lines("cd docs", "exit")
        self.assertEqual(shell.out.getvalue(), "cd: args=['docs']\n")

    def test_environment_variable_in_arguments(self):
        """Переменные окружения раскрываются до вызова команды."""
        shell, _ = run_lines("cd $HOME", "exit", env={"HOME": "/home/u"})
        self.assertEqual(shell.out.getvalue(), "cd: args=['/home/u']\n")

    def test_unset_variable_gives_no_argument(self):
        """Неизвестная переменная не создаёт пустой аргумент."""
        shell, _ = run_lines("ls $NOPE x", "exit")
        self.assertEqual(shell.out.getvalue(), "ls: args=['x']\n")

    def test_quoted_argument_is_one_word(self):
        """Аргумент в кавычках передаётся одним словом."""
        shell, _ = run_lines('ls "a b" c', "exit")
        self.assertEqual(shell.out.getvalue(), "ls: args=['a b', 'c']\n")


class ErrorHandlingTest(unittest.TestCase):
    """Ошибки сообщаются пользователю, цикл продолжает работу."""

    def test_unknown_command(self):
        """Неизвестная команда даёт сообщение об ошибке."""
        shell, _ = run_lines("foo bar", "exit")
        self.assertEqual(shell.err.getvalue(), "foo: command not found\n")
        self.assertEqual(shell.out.getvalue(), "")

    def test_work_continues_after_error(self):
        """После ошибки следующая команда выполняется."""
        shell, _ = run_lines("foo", "cd x", "exit")
        self.assertEqual(shell.out.getvalue(), "cd: args=['x']\n")

    def test_parse_error_is_reported(self):
        """Незакрытая кавычка не роняет эмулятор."""
        shell, _ = run_lines("ls 'abc", "ls ok", "exit")
        self.assertIn("syntax error", shell.err.getvalue())
        self.assertEqual(shell.out.getvalue(), "ls: args=['ok']\n")

    def test_blank_and_comment_lines(self):
        """Пустые строки и комментарии ничего не делают."""
        shell, _ = run_lines("", "   ", "# just a comment", "exit")
        self.assertEqual(shell.out.getvalue(), "")
        self.assertEqual(shell.err.getvalue(), "")


class ExitTest(unittest.TestCase):
    """Команда exit и завершение по концу ввода."""

    def test_exit_default_code(self):
        """exit без аргументов завершает работу с кодом 0."""
        _, code = run_lines("exit")
        self.assertEqual(code, 0)

    def test_exit_with_code(self):
        """exit N завершает работу с кодом N."""
        _, code = run_lines("exit 3")
        self.assertEqual(code, 3)

    def test_exit_code_is_masked(self):
        """Код возврата берётся по модулю 256, как в UNIX."""
        _, code = run_lines("exit 257")
        self.assertEqual(code, 1)

    def test_exit_non_numeric(self):
        """Нечисловой аргумент: сообщение об ошибке и код 2."""
        shell, code = run_lines("exit abc")
        self.assertEqual(code, 2)
        self.assertIn("numeric argument required", shell.err.getvalue())

    def test_exit_too_many_arguments(self):
        """Лишние аргументы: ошибка, эмулятор продолжает работу."""
        shell, code = run_lines("exit 1 2", "ls", "exit 5")
        self.assertIn("too many arguments", shell.err.getvalue())
        self.assertEqual(shell.out.getvalue(), "ls: args=[]\n")
        self.assertEqual(code, 5)

    def test_end_of_input(self):
        """Конец ввода (Ctrl-D) завершает работу и пишет exit."""
        shell, code = run_lines()
        self.assertEqual(shell.out.getvalue(), "exit\n")
        self.assertEqual(code, 0)

    def test_interrupt_keeps_running(self):
        """Ctrl-C сбрасывает ввод, но не завершает эмулятор."""
        shell, code = run_lines(KeyboardInterrupt(), "ls", "exit 4")
        self.assertEqual(shell.out.getvalue(), "\nls: args=[]\n")
        self.assertEqual(code, 4)


if __name__ == "__main__":
    unittest.main()
