"""Ядро эмулятора: приглашение к вводу, выполнение строк, цикл REPL."""

from __future__ import annotations

import getpass
import os
import socket
import sys
from typing import Callable, Mapping, TextIO

from .commands import COMMANDS, EXIT_OK
from .errors import ShellError
from .parser import parse_line
from .vfs import Vfs

DEFAULT_USER = "user"


def build_prompt() -> str:
    """Формирует приглашение вида user@host:~$ из данных реальной ОС."""
    try:
        user = getpass.getuser()
    except (KeyError, OSError):
        user = DEFAULT_USER
    return f"{user}@{socket.gethostname()}:~$ "


class Shell:
    """Состояние эмулятора и выполнение команд пользователя."""

    def __init__(
        self,
        env: Mapping[str, str] | None = None,
        prompt: str | None = None,
        read_line: Callable[[str], str] = input,
        out: TextIO | None = None,
        err: TextIO | None = None,
        vfs: Vfs | None = None,
    ) -> None:
        """Создаёт оболочку; параметры позволяют подменить ввод и вывод."""
        self.env = dict(os.environ if env is None else env)
        self.prompt = build_prompt() if prompt is None else prompt
        self.read_line = read_line
        self.out = sys.stdout if out is None else out
        self.err = sys.stderr if err is None else err
        self.vfs = Vfs.default() if vfs is None else vfs
        self.exit_code: int | None = None
        self.commands = dict(COMMANDS)

    def write(self, text: str = "") -> None:
        """Выводит строку в поток вывода."""
        print(text, file=self.out)

    def error(self, text: str) -> None:
        """Выводит сообщение в поток ошибок."""
        print(text, file=self.err)

    def execute(self, line: str) -> None:
        """Разбирает и выполняет одну строку; ошибки передаёт вызывающему."""
        words = parse_line(line, self.env)
        if not words:
            return
        handler = self.commands.get(words[0])
        if handler is None:
            raise ShellError(f"{words[0]}: command not found")
        handler(self, words[1:])

    def run_line(self, line: str) -> None:
        """Выполняет строку, показывая ошибку и не прерывая работу."""
        try:
            self.execute(line)
        except ShellError as exc:
            self.error(str(exc))

    def run(self) -> int:
        """Читает и выполняет команды до exit или конца ввода."""
        while self.exit_code is None:
            try:
                line = self.read_line(self.prompt)
            except EOFError:
                self.write("exit")
                self.exit_code = EXIT_OK
            except KeyboardInterrupt:
                self.write()
            else:
                self.run_line(line)
        return self.exit_code
