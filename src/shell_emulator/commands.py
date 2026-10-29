"""Команды эмулятора."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from .errors import ShellError, VfsError

if TYPE_CHECKING:
    from .shell import Shell

EXIT_OK = 0
EXIT_MISUSE = 2
EXIT_MASK = 0xFF
EXIT_MAX_ARGS = 1
VFS_SAVE_ARGS = 1

Handler = Callable[["Shell", "list[str]"], None]


def show_stub(shell: Shell, name: str, args: list[str]) -> None:
    """Выводит имя команды-заглушки и список её аргументов."""
    shell.write(f"{name}: args={args}")


def cmd_ls(shell: Shell, args: list[str]) -> None:
    """Заглушка ls: выводит своё имя и аргументы."""
    show_stub(shell, "ls", args)


def cmd_cd(shell: Shell, args: list[str]) -> None:
    """Заглушка cd: выводит своё имя и аргументы."""
    show_stub(shell, "cd", args)


def exit_status(shell: Shell, args: list[str]) -> int:
    """Вычисляет код возврата для exit; сообщает о нечисловом аргументе."""
    if not args:
        return EXIT_OK
    try:
        return int(args[0]) & EXIT_MASK
    except ValueError:
        shell.error(f"exit: {args[0]}: numeric argument required")
        return EXIT_MISUSE


def cmd_exit(shell: Shell, args: list[str]) -> None:
    """exit [код]: завершает работу эмулятора с указанным кодом."""
    if len(args) > EXIT_MAX_ARGS:
        raise ShellError("exit: too many arguments")
    shell.exit_code = exit_status(shell, args)


def cmd_vfs_save(shell: Shell, args: list[str]) -> None:
    """vfs-save ПУТЬ: сохраняет состояние VFS на диск в исходном формате."""
    if not args:
        raise ShellError("vfs-save: missing path operand")
    if len(args) > VFS_SAVE_ARGS:
        raise ShellError("vfs-save: too many arguments")
    try:
        shell.vfs.save(args[0])
    except VfsError as exc:
        raise ShellError(f"vfs-save: {exc}") from exc
    shell.write(f"VFS saved to {args[0]}")


COMMANDS: dict[str, Handler] = {
    "ls": cmd_ls,
    "cd": cmd_cd,
    "exit": cmd_exit,
    "vfs-save": cmd_vfs_save,
}
