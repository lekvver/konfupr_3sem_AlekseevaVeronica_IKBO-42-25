"""Выполнение стартового скрипта с имитацией диалога с пользователем."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import ShellError

if TYPE_CHECKING:
    from .shell import Shell

SCRIPT_ENCODING = "utf-8-sig"


def read_script(path: str) -> list[str]:
    """Читает стартовый скрипт и возвращает его строки.

    Если файл нельзя прочитать, возбуждает ShellError с причиной.
    """
    try:
        with open(path, encoding=SCRIPT_ENCODING) as stream:
            return stream.read().splitlines()
    except OSError as exc:
        reason = exc.strerror or str(exc)
    except UnicodeDecodeError:
        reason = "not a UTF-8 text file"
    raise ShellError(f"cannot read startup script {path}: {reason}")


def run_script(shell: Shell, path: str) -> None:
    """Выполняет команды скрипта по очереди.

    Каждая непустая строка выводится с приглашением, как будто её набрал
    пользователь, затем показывается результат. Ошибочная строка
    пропускается: об ошибке сообщается с номером строки, выполнение
    продолжается. После команды exit скрипт прерывается.
    """
    for number, line in enumerate(read_script(path), start=1):
        if shell.exit_code is not None:
            break
        if not line.strip():
            continue
        shell.write(f"{shell.prompt}{line}")
        try:
            shell.execute(line)
        except ShellError as exc:
            shell.error(f"{path}: line {number}: {exc}")
