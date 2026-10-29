"""Вспомогательные функции для тестов."""

import io

from shell_emulator.shell import Shell

TEST_PROMPT = "user@host:~$ "


def make_shell(lines=(), env=None):
    """Создаёт оболочку: ввод берётся из lines, вывод идёт в буферы.

    Элемент списка может быть исключением, тогда оно будет возбуждено
    при чтении (так имитируются Ctrl-C и Ctrl-D). Когда строки кончились,
    возникает EOFError.
    """
    feed = iter(lines)

    def read_line(prompt):
        """Отдаёт очередную строку или сигнал конца ввода."""
        try:
            item = next(feed)
        except StopIteration:
            raise EOFError from None
        if isinstance(item, BaseException):
            raise item
        return item

    return Shell(
        env={} if env is None else env,
        prompt=TEST_PROMPT,
        read_line=read_line,
        out=io.StringIO(),
        err=io.StringIO(),
    )
